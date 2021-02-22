# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import logging
import re

from datetime import datetime
from html import unescape
from io import BytesIO

from lxml import etree

from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

try:
    import pdf417gen
except ImportError:
    pdf417gen = None
    _logger.error('Could not import library pdf417gen')


class Picking(models.Model):
    _name = 'stock.picking'
    _inherit = ['l10n_cl.edi.util', 'stock.picking']

    # TODO: Translations
    l10n_cl_delivery_guide_reason = fields.Selection([
            ('1', '1. Operación constituye venta'),
            ('2', '2. Ventas por efectuar'),
            ('3', '3. Consignaciones'),
            ('4', '4. Entrega Gratuita'),
            ('5', '5. Traslados Internos'),
            ('6', '6. Otros traslados no venta'),
            ('7', '7. Guía de Devolución'),
            ('8', '8. Traslado para exportación'),
            ('9', '9. Ventas para exportación')
        ], string='Reason of the Transfer', default='2')

    l10n_latam_document_type_id = fields.Many2one('l10n_latam.document.type', string='Document Type',copy=False)
    l10n_latam_document_number = fields.Char(string='Delivery Guide Number', copy=False)
    l10n_cl_draft_status = fields.Boolean()
    l10n_cl_reference_ids = fields.One2many('l10n_cl.account.invoice.reference', 'picking_id', readonly=True,
                                            states={'draft': [('readonly', False)]}, string='Reference Records')
    l10n_cl_dte_status = fields.Selection([
            ('not_sent', 'Pending To Be Sent'),
            ('ask_for_status', 'Ask For Status'),
            ('accepted', 'Accepted'),
            ('objected', 'Accepted With Objections'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled'),
            ('manual', 'Manual')], string= "Status SII")
    l10n_cl_dte_file = fields.Many2one('ir.attachment', string='DTE file', copy=False)
    l10n_cl_sii_send_file = fields.Many2one('ir.attachment', string='SII Send file', copy=False)
    l10n_cl_sii_send_ident = fields.Text(string='SII Send Identification(Track ID)', readonly=True,
                                         states={'draft': [('readonly', False)]}, copy=False, tracking=True)
    as_amount_total = fields.Float(string='Monto total')
    journal_id = fields.Many2one('account.journal')
    date_invoice = fields.Date(
        string='Refund Date',
        default=fields.Date.context_today,
        required=True
    )
    invoice_date = fields.Date(
        string='Fecha de Movimiento',
        default=fields.Date.context_today,
        required=True
    )

    l10n_cl_sii_barcode = fields.Char(
        string='SII Barcode', readonly=True, copy=False,
        help='This XML contains the portion of the DTE XML that should be coded in PDF417 '
             'and printed in the invoice barcode should be present in the printed invoice report to be valid')
    as_use_document = fields.Boolean(string='Usa Documentos Tributarios', copy=False)

    def button_validate(self):
        res = super().button_validate()
        if self.as_use_document:
            self.create_delivery_guide()
        return res

    @api.onchange('as_use_document')
    def get_docuemnt_type(self):
        self.l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search([('code','=',52)])
        self.l10n_cl_dte_status = 'manual'

        
    def write(self, vals):
        total = 0.0
        for move in self.move_ids_without_package:
            total += move.price_unit * move.product_uom_qty
        vals['as_amount_total'] = total
        
        rslt = super(Picking, self).write(vals)

    def action_cancel(self):
        for record in self.filtered(lambda x: x.company_id.country_id == self.env.ref('base.cl') and
                                              x.l10n_cl_dte_status):
            # The move cannot be modified once the DTE has been accepted by the SII
            if record.l10n_cl_dte_status == 'accepted':
                raise UserError(_('%s is accepted by SII. It cannot be cancelled.') % self.name)
            record.l10n_cl_dte_status = 'cancelled'
        return super().action_cancel()

    def _create_new_sequence(self):
        caf_file = self.env['l10n_cl.dte.caf'].search([
            ('company_id', '=', self.company_id.id), ('status', '=', 'in_use'),
            ('l10n_latam_document_type_id', '=', self.l10n_latam_document_type_id.id)])
        if not caf_file:
            raise UserError(_('CAF file for the document type %s not found. Please, upload a caf file before to '
                              'create the delivery guide') % self.l10n_latam_document_type_id.code)
        return self.env['ir.sequence'].create({
            'name': 'Stock Picking CAF Sequence',
            'code': 'l10n_cl_edi_stock.stock_picking_caf_sequence',
            'padding': 6,
            'company_id': self.company_id.id,
            'number_next': int(self.l10n_latam_document_number) + 1
        })

    def l10n_cl_verify_dte_status(self, send_dte_to_partner=True): #funcion traida de util porque es llamada en la vista
        digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
        response = self._get_send_status(
            self.company_id.l10n_cl_dte_service_provider,
            self.l10n_cl_sii_send_ident,
            self._l10n_cl_format_vat(self.company_id.vat),
            digital_signature)
        if not response:
            self.l10n_cl_dte_status = 'ask_for_status'
            digital_signature.last_token = False
            return None

        response_parsed = etree.fromstring(response.encode('utf-8'))
        self.l10n_cl_dte_status = self._analyze_sii_result(response_parsed)
        if self.l10n_cl_dte_status in ['accepted', 'objected']:
            self.l10n_cl_dte_partner_status = 'not_sent'
            if send_dte_to_partner:
                self._l10n_cl_send_dte_to_partner()
        if response_parsed.findtext('{http://www.sii.cl/XMLSchema}RESP_HDR/ESTADO') in ['001', '002', '003']:
            digital_signature.last_token = False
            _logger.error('Token is invalid.')
        else:
            self.message_post(
                body=_('Asking for DTE status with response:') +
                     '<br /><li><b>ESTADO</b>: %s</li><li><b>GLOSA</b>: %s</li><li><b>NUM_ATENCION</b>: %s</li>' % (
                         response_parsed.findtext('{http://www.sii.cl/XMLSchema}RESP_HDR/ESTADO'),
                         response_parsed.findtext('{http://www.sii.cl/XMLSchema}RESP_HDR/GLOSA'),
                         response_parsed.findtext('{http://www.sii.cl/XMLSchema}RESP_HDR/NUM_ATENCION')))


    def l10n_cl_send_dte_to_sii(self, retry_send=True): #funcion traida de util porque es llamada en la vista
        """
        Send the DTE to the SII. It will be
        """
        digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
        response = self._send_xml_to_sii(
            self.company_id.l10n_cl_dte_service_provider,
            self.company_id.website,
            self.company_id.vat,
            self.l10n_cl_sii_send_file.name,
            base64.b64decode(self.l10n_cl_sii_send_file.datas),
            digital_signature
        )
        if not response:
            return None

        response_parsed = etree.fromstring(response)
        self.l10n_cl_sii_send_ident = response_parsed.findtext('TRACKID')
        sii_response_status = response_parsed.findtext('STATUS')
        if sii_response_status == '5':
            digital_signature.last_token = False
            _logger.error('The response status is %s. Clearing the token.' %
                          self._l10n_cl_get_sii_reception_status_message(sii_response_status))
            if retry_send:
                _logger.info('Retrying send DTE to SII')
                self.l10n_cl_send_dte_to_sii(retry_send=False)

            # cleans the token and keeps the l10n_cl_dte_status until new attempt to connect
            # would like to resend from here, because we cannot wait till tomorrow to attempt
            # a new send
        else:
            self.l10n_cl_dte_status = 'ask_for_status' if sii_response_status == '0' else 'rejected'
        self.message_post(body=_('DTE has been sent to SII with response: %s.') %
                               self._l10n_cl_get_sii_reception_status_message(sii_response_status))


    def _get_next_document_number(self):
        sequence = self.env['ir.sequence'].search([
            ('code', '=', 'l10n_cl_edi_stock.stock_picking_caf_sequence'), ('company_id', '=', self.company_id.id)])
        if not sequence:
            sequence = self._create_new_sequence()
        return self.l10n_latam_document_number or sequence.next_by_id()

    # def create_delivery_guide(self):
    #     self.l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search([('code','=',52)])
    #     for record in self.filtered(
    #             lambda x: x.company_id.country_id == self.env.ref('base.cl') and
    #                       x.company_id.l10n_cl_dte_service_provider in ['SII', 'SIITEST']):
    #         record._l10n_cl_create_delivery_guide_validation()
    #         if record.partner_id.l10n_cl_delivery_guide_price_list is None:
    #             raise UserError(_('Please, configure the Delivery Guide Price List in the partner.'))

    #         document_type = self.env['l10n_latam.document.type'].search([('code', '=', 52)], limit=1)
    #         if not document_type:
    #             raise UserError('Document type with code 52 active not found.')

    #         if not record.l10n_latam_document_number and not self.env['ir.sequence'].search(
    #                 [('code', '=', 'l10n_cl_edi_stock.stock_picking_caf_sequence')]):
    #             record.l10n_cl_draft_status = True
    #             return None

    #         record.l10n_latam_document_type_id = document_type.id
    #         record.l10n_cl_dte_status = 'not_sent'

    #         record.l10n_latam_document_number = record._get_next_document_number()
    #         record.l10n_cl_draft_status = False
    #         record._l10n_cl_create_dte()
    #         dte_signed, file_name = record._l10n_cl_get_dte_envelope()
    #         attachment = self.env['ir.attachment'].create({
    #             'name': 'SII_{}'.format(file_name),
    #             'name': 'SII_{}'.format(file_name),
    #             'res_id': record.id,
    #             'res_model': self._name,
    #             'datas': base64.b64encode(dte_signed.encode('ISO-8859-1')),
    #             'type': 'binary',
    #         })
    #         record.l10n_cl_sii_send_file = attachment.id
    #         # TODO: print pdf
    #         record.message_post(body=_('DTE has been created'), attachment_ids=attachment.ids)

    def create_delivery_guide(self):
        for record in self.filtered(
                lambda x: x.company_id.country_id == self.env.ref('base.cl') and
                          x.company_id.l10n_cl_dte_service_provider in ['SII', 'SIITEST']):
            record._l10n_cl_create_delivery_guide_validation()
            if record.partner_id.l10n_cl_delivery_guide_price is None:
                raise UserError(_('Please, configure the Delivery Guide Price in the partner.'))

            document_type = self.env['l10n_latam.document.type'].search([('code', '=', 52)], limit=1)
            if not document_type:
                raise UserError('Document type with code 52 active not found.')

            if not record.l10n_latam_document_number and not self.env['ir.sequence'].search(
                    [('code', '=', 'l10n_cl_edi_stock.stock_picking_caf_sequence')]):
                record.l10n_cl_draft_status = True
                return None

            record.l10n_latam_document_type_id = document_type.id
            record.l10n_cl_dte_status = 'not_sent'

            record.l10n_latam_document_number = record._get_next_document_number()
            record.l10n_cl_draft_status = False
            record._l10n_cl_create_dte()
            dte_signed, file_name = record._l10n_cl_get_dte_envelope()
            attachment = self.env['ir.attachment'].create({
                'name': 'SII_{}'.format(file_name),
                'res_id': record.id,
                'res_model': self._name,
                'datas': base64.b64encode(dte_signed.encode('ISO-8859-1')),
                'type': 'binary',
            })
            record.l10n_cl_sii_send_file = attachment.id
            # TODO: print pdf
            record.message_post(body=_('DTE has been created'), attachment_ids=attachment.ids)

    def print_delivery_guide_pdf(self):
        return self.env.ref('l10n_cl_edi_stock.delivery_guide_report_pdf').report_action(self)

    def _l10n_cl_get_sii_reception_status_message(self, sii_response_status):
        """
        Get the value of the code returns by SII once the DTE has been sent to the SII.
        """
        return {
            '0': _('Upload OK'),
            '1': _('Sender Does Not Have Permission To Send'),
            '2': _('File Size Error (Too Big or Too Small)'),
            '3': _('Incomplete File (Size <> Parameter size)'),
            '5': _('Not Authenticated'),
            '6': _('Company Not Authorized to Send Files'),
            '7': _('Invalid Schema'),
            '8': _('Document Signature'),
            '9': _('System Locked'),
            'Otro': _('Internal Error'),
        }.get(sii_response_status, sii_response_status)

    def _pdf417_barcode(self, barcode_data):
        #  This method creates the graphic representation of the barcode
        barcode_file = BytesIO()
        if pdf417gen is None:
            return False
        bc = pdf417gen.encode(barcode_data, security_level=5, columns=13)
        image = pdf417gen.render_image(bc, padding=15, scale=1)
        image.save(barcode_file, 'PNG')
        data = barcode_file.getvalue()
        return base64.b64encode(data)


    def _l10n_cl_get_dte_envelope(self, receiver_rut='60803000-K'):
        file_name = 'F{}T{}.xml'.format(self.l10n_latam_document_number, self.l10n_latam_document_type_id.code)
        digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
        template = self.l10n_latam_document_type_id._is_doc_type_voucher() and self.env.ref(
            'l10n_cl_edi.envio_boleta') or self.env.ref('l10n_cl_edi.envio_dte')
        dte_rendered = template._render({
            'move': self,
            'RutEmisor': self._l10n_cl_format_vat(self.company_id.vat),
            'RutEnvia': digital_signature.subject_serial_number,
            'RutReceptor': receiver_rut,
            'FchResol': self.company_id.l10n_cl_dte_resolution_date,
            'NroResol': self.company_id.l10n_cl_dte_resolution_number,
            'TmstFirmaEnv': self._get_cl_current_strftime(),
            'dte': base64.b64decode(self.l10n_cl_dte_file.datas).decode('ISO-8859-1')
        })
        dte_rendered = unescape(dte_rendered.decode('utf-8')).replace('<?xml version="1.0" encoding="ISO-8859-1" ?>', '')
        dte_signed = self._sign_full_xml(
            dte_rendered, digital_signature, 'SetDoc',
            self.l10n_latam_document_type_id._is_doc_type_voucher() and 'bol' or 'env',
            self.l10n_latam_document_type_id._is_doc_type_voucher()
        )
        return dte_signed, file_name

    # def _l10n_cl_get_dte_envelope(self, receiver_rut='60803000-K'):
    #     file_name = 'F{}T{}.xml'.format(self.l10n_latam_document_number, self.l10n_latam_document_type_id.code)
    #     digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
    #     template = self.l10n_latam_document_type_id._is_doc_type_voucher() and self.env.ref(
    #         'l10n_cl_edi.envio_boleta') or self.env.ref('l10n_cl_edi_stock.envio_dte')
    #     dte_rendered = template._render({
    #         'move': self,
    #         'RutEmisor': self._l10n_cl_format_vat(self.company_id.vat),
    #         'RutEnvia': digital_signature.subject_serial_number,
    #         'RutReceptor': receiver_rut,
    #         'FchResol': self.company_id.l10n_cl_dte_resolution_date,
    #         'NroResol': self.company_id.l10n_cl_dte_resolution_number,
    #         'TmstFirmaEnv': self._get_cl_current_strftime(),
    #         'dte': base64.b64decode(self.l10n_cl_dte_file.datas).decode('ISO-8859-1')
    #     })
    #     dte_rendered = unescape(dte_rendered.decode('utf-8')).replace('<?xml version="1.0" encoding="ISO-8859-1" ?>', '')
    #     dte_signed = self._sign_full_xml(
    #         dte_rendered, digital_signature, 'SetDoc',
    #         self.l10n_latam_document_type_id._is_doc_type_voucher() and 'bol' or 'env',
    #         self.l10n_latam_document_type_id._is_doc_type_voucher()
    #     )
    #     return dte_signed, file_name

    def l10n_cl_confirm_draft_delivery_guide(self):
        for record in self:
            record.l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search([('code','=',52)])
            record.create_delivery_guide()
            record.l10n_cl_draft_status = False

    def l10n_cl_set_delivery_guide_to_draft(self):
        for record in self:
            record.l10n_cl_draft_status = True
            record.l10n_cl_dte_status = None
            record.l10n_cl_sii_send_file = None

    # DTE creation
    def _l10n_cl_get_comuna_recep(self):
        if self.partner_id._l10n_cl_is_foreign():
            return self._format_length(
                self.partner_id.state_id.name or self.partner_id.state_id.name or 'N-A', 20)
        if self.l10n_latam_document_type_id._is_doc_type_voucher():
            return 'N-A'
        return self.partner_id.city or self.partner_id.city or False

    def _l10n_cl_get_set_dte_id(self, xml_content):
        set_dte = xml_content.find('.//ns0:SetDTE', namespaces={'ns0': 'http://www.sii.cl/SiiDte'})
        set_dte_attrb = set_dte and set_dte.attrib or {}
        return set_dte_attrb.get('ID', '')


    def _l10n_cl_create_dte(self):
        sii_barcode, signed_dte = self._l10n_cl_get_signed_dte()
        self.l10n_cl_sii_barcode = sii_barcode
        dte_attachment = self.env['ir.attachment'].create({
            'name': 'DTE_{}.xml'.format(self.l10n_latam_document_number),
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
            'datas': base64.b64encode(signed_dte.encode('ISO-8859-1'))
        })
        self.l10n_cl_dte_file = dte_attachment.id

    def _l10n_cl_get_signed_dte(self):
        folio = int(self.l10n_latam_document_number)
        doc_id_number = 'F{}T{}'.format(folio, self.l10n_latam_document_type_id.code)
        caf_file = self.l10n_latam_document_type_id._get_caf_file(self.company_id.id,
                                                                  int(self.l10n_latam_document_number))
        dte_barcode_xml = self._l10n_cl_get_dte_barcode_xml(caf_file)
        dte = self.env.ref('l10n_cl_edi.dte_template')._render({
            'move': self,
            'format_vat': self._l10n_cl_format_vat,
            'get_cl_current_strftime': self._get_cl_current_strftime,
            'format_length': self._format_length,
            'doc_id': doc_id_number,
            'caf': self.l10n_latam_document_type_id._get_caf_file(self.company_id.id, int(self.l10n_latam_document_number)),
            'amounts': self._l10n_cl_get_amounts(),
            'withholdings': self._l10n_cl_get_withholdings(),
            'dte': dte_barcode_xml['ted'],
        })
        dte = unescape(dte.decode('utf-8')).replace(r'&', '&amp;')
        digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
        signed_dte = self._sign_full_xml(
            dte, digital_signature, doc_id_number, 'doc', self.l10n_latam_document_type_id._is_doc_type_voucher())

        return dte_barcode_xml['barcode'], signed_dte

    def _l10n_cl_get_dte_barcode_xml(self, caf_file):
        """
        This method create the "stamp" (timbre). Is the auto-contained information inside the pdf417 barcode, which
        consists of a reduced xml version of the invoice, containing: issuer, recipient, folio and the first line
        of the invoice, etc.
        :return: xml that goes embedded inside the pdf417 code
        """
        dd = self.env.ref('l10n_cl_edi.dd_template')._render({
            'move': self,
            'format_vat': self._l10n_cl_format_vat,
            'format_length': self._format_length,
            'time_stamp': self._get_cl_current_strftime(),
            'caf': caf_file
        })
        dd = dd.replace(rb'&amp;', b'&')
        ted = self.env.ref('l10n_cl_edi.ted_template')._render({
            'dd': dd,
            'frmt': self._sign_message(dd.decode('utf-8').encode('ISO-8859-1'), caf_file.findtext('RSASK')),
            'stamp': self._get_cl_current_strftime()
        })
        ted = unescape(ted.decode('utf-8'))
        return {
            'ted': re.sub(r'\n\s*$', '', ted, flags=re.MULTILINE),
            'barcode': etree.tostring(etree.fromstring(re.sub(
                r'<TmstFirma>.*</TmstFirma>', '', ted.replace('&', '&amp;')), parser=etree.XMLParser(remove_blank_text=True)))
        }

    def _l10n_cl_create_delivery_guide_validation(self):
        if self.partner_id._l10n_cl_is_foreign():
            raise UserError(_(
                'Delivery Guide for foreign partner is not implemented yet'
            ))
        if not self.company_id.l10n_cl_company_activity_ids:
            raise UserError(_(
                'There are no activity codes configured in your company. This is mandatory for electronic '
                'delivery guide. Please go to your company and set the correct activity codes (www.sii.cl - Mi SII)'))
        if not self.company_id.l10n_cl_sii_regional_office:
            raise UserError(_(
                'There is no SII Regional Office configured in your company. This is mandatory for electronic '
                'delivery guide. Please go to your company and set the regional office, according to your company '
                'address (www.sii.cl - Mi SII)'))
        if not self.company_id.partner_id.city:
            raise UserError(_(
                'There is no city configured in your partner company. This is mandatory for electronic'
                'delivery guide. Please go to your partner company and set the city.'
            ))
        if not self.company_id.l10n_cl_activity_description:
            raise UserError(_(
                'Your company has not an activity description configured. This is mandatory for electronic '
                'delivery guide. Please go to your company and set the correct one (www.sii.cl - Mi SII)'))
        if not self.partner_id.l10n_cl_activity_description:
            raise UserError(_(
                'There is not an activity description configured in the '
                'customer record. This is mandatory for electronic delivery guide for this type of '
                'document. Please go to the partner record and set the activity description'))
        if not self.partner_id.street:
            raise UserError(_(
                'There is no address configured in your customer record. '
                'This is mandatory for electronic delivery guide for this type of document. '
                'Please go to the partner record and set the address'))

    # TODO: get the amounts with different product UOM
    def _l10n_cl_get_amounts(self):
        """
        This method is used to calculate the amount and taxes required in the Chilean localization electronic documents.
        """
        self.ensure_one()
        if self.partner_id.l10n_cl_delivery_guide_price == 'no_price':
            return {
                'vat_amount': 0,
                'subtotal_amount_taxable': 0,
                'subtotal_amount_exempt': 0,
                'vat_percent': False,
                'total_amount': 0,
            }
        values = {}
        if self.partner_id.l10n_cl_delivery_guide_price == 'product_price' or (
                self.partner_id.l10n_cl_delivery_guide_price == 'sale_order_price' and not self.sale_id):
            lines_with_taxes = self.move_lines.filtered(lambda x: x.product_id.taxes_id.filtered(
                lambda y: y.l10n_cl_sii_code == 14))
            lines_without_taxes = self.move_lines.filtered(lambda x: not x.product_id.taxes_id)
            if lines_with_taxes:
                tax_id = self.move_lines.product_id.taxes_id.filtered(lambda x: x.l10n_cl_sii_code == 14)
                values.update({
                    'vat_amount': sum(self.company_id.currency_id.round(
                        line.product_id.lst_price * line.product_qty * tax_id.amount / 100) for line in lines_with_taxes),
                    'subtotal_amount_taxable': sum(self.company_id.currency_id.round(
                        line.product_id.lst_price * line.product_qty) for line in lines_with_taxes),
                    'vat_percent': '%.2f' % tax_id.amount
                })
            if lines_without_taxes:
                values.update({'subtotal_amount_exempt': sum(self.company_id.currency_id.round(
                        line.product_id.lst_price * line.product_qty) for line in lines_without_taxes)})

            values['total_amount'] = self.company_id.currency_id.round(
                values.get('subtotal_amount_taxable', 0) + values.get('vat_amount', 0) + values.get('subtotal_amount_exempt', 0))
        elif self.partner_id.l10n_cl_delivery_guide_price == 'sale_order_price':
            lines_with_taxes = self.sale_id.order_line.filtered(lambda x: x.tax_id.filtered(lambda y: y.l10n_cl_sii_code == 14))
            lines_without_taxes = self.sale_id.order_line.filtered(lambda x: not x.tax_id)
            if lines_with_taxes:
                tax_id = self.move_lines.product_id.taxes_id.filtered(lambda x: x.l10n_cl_sii_code == 14)
                values.update({
                    'vat_percent': '%.2f' % tax_id.amount,
                    'vat_amount': 0,
                    'subtotal_amount_taxable': 0,
                })
                for line in lines_with_taxes:
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.filtered(lambda x: x.l10n_cl_sii_code == 14).compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                product=line.product_id, partner=line.order_id.partner_shipping_id)
                    values['vat_amount'] += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                    values['subtotal_amount_taxable'] += taxes['total_excluded']
            if lines_without_taxes:
                values.update({'subtotal_amount_exempt': sum(lines_without_taxes.mapped('price_subtotal'))})
            values['total_amount'] = self.sale_id.amount_total
        return values


    # FIXME: wip
    def _l10n_cl_get_withholdings(self):
        """
        This method calculates the section of withholding taxes, or 'other' taxes for the Chilean electronic invoices.
        These taxes are not VAT taxes in general; they are special taxes (for example, alcohol or sugar-added beverages,
        withholdings for meat processing, fuel, etc.
        The taxes codes used are included here:
        [15, 17, 18, 19, 24, 25, 26, 27, 271]
        http://www.sii.cl/declaraciones_juradas/ddjj_3327_3328/cod_otros_imp_retenc.pdf
        The need of the tax is not just the amount, but the code of the tax, the percentage amount and the amount
        :return:
        """
        self.ensure_one()
        values = []
        if self.partner_id._l10n_cl_is_delivery_guide_with_no_price():
            return values
        if self.partner_id._l10n_cl_is_delivery_guide_with_sale_order_price() and self.sale_id:
            lines_with_withholding_taxes = self.sale_id.order_line.filtered(lambda x: x.tax_id.filtered(
                lambda y: y.tax_group_id.id in [self.env.ref('l10n_cl.tax_group_ila').id, self.env.ref('l10n_cl.tax_group_retenciones').id]))
            for line in lines_with_withholding_taxes:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                for tax in line.tax_id.filtered(lambda x: x.tax_group_id.id in [self.env.ref(
                        'l10n_cl.tax_group_ila').id, self.env.ref('l10n_cl.tax_group_retenciones').id]):
                    tax_amounts = tax.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                      product=line.product_id, partner=line.order_id.partner_shipping_id)
                    values.append({
                        'tax_code': tax.l10n_cl_sii_code,
                        'tax_percent': tax.amount,
                        'tax_amount': sum(t.get('amount', 0.0) for t in tax_amounts.get('taxes', []))
                    })
            return values

        lines_with_withholding_taxes = self.move_lines.filtered(lambda x: x.product_id.taxes_id.filtered(
                lambda y: y.tax_group_id.id in [self.env.ref('l10n_cl.tax_group_ila').id,
                                            self.env.ref('l10n_cl.tax_group_retenciones').id]))
        for line in lines_with_withholding_taxes:
            for tax in line.tax_id.filtered(lambda x: x.tax_group_id.id in [self.env.ref(
                    'l10n_cl.tax_group_ila').id, self.env.ref('l10n_cl.tax_group_retenciones').id]):
                values.append({
                    'tax_code': tax.l10n_cl_sii_code,
                    'tax_percent': tax.amount,
                    'tax_amount': sum(self.company_id.currency_id.round(line.product_id.lst_price * line.product_qty * tax.amount / 100)),
                })
        return values

    # Cron methods


    def _l10n_cl_ask_dte_status(self):
        super(Picking, self)._l10n_cl_ask_dte_status()
        for picking in self.search([('l10n_cl_dte_status', '=', 'ask_for_status')]):
            picking.l10n_cl_verify_dte_status(send_dte_to_partner=False)
            self.env.cr.commit()

    # cron jobs
    def cron_run_sii_workflow(self):
        super(Picking, self).cron_run_sii_workflow()
        self_skip = self.with_context(cron_skip_connection_errs=True)
        self_skip._l10n_cl_ask_dte_status()
        # self_skip._l10n_cl_send_dte_to_partner_multi()

    def cron_send_dte_to_sii(self):
        super(Picking, self).cron_send_dte_to_sii()
        for record in self.search([('l10n_cl_dte_status', '=', 'not_sent')]):
            record.with_context(cron_skip_connection_errs=True).l10n_cl_send_dte_to_sii()
            self.env.cr.commit()


class StockMove(models.Model):
    _inherit = "stock.move"

    discount = fields.Float(string='Descuento')
    price_subtotal = fields.Float(string='Price_subtotal')

    def _is_line_exempt(self):
        if self.partner_id._l10n_cl_is_delivery_guide_with_sale_order_price() and self.sale_line_id:
            return not self.sale_line_id.tax_id
        return not self.product_id.taxes_id

    def _l10n_cl_get_product_price(self):
        if self.partner_id._l10n_cl_is_delivery_guide_with_no_price():
            return 0
        if self.partner_id._l10n_cl_is_delivery_guide_with_sale_order_price() and self.sale_line_id:
            return self.sale_line_id.price_unit
        return self.product_id.lst_price

    def _l10n_cl_get_withholdings_taxes(self):
        if self.partner_id._l10n_cl_is_delivery_guide_with_no_price():
            return []
        tax_ids = self.sale_line_id.tax_id if (self.partner_id._l10n_cl_is_delivery_guide_with_sale_order_price() and
                                               self.sale_line_id) else self.product_id.taxes_id

        return tax_ids.filtered(lambda x: x.l10n_cl_sii_code in [24, 25, 26, 27])

    def _l10n_cl_get_line_amounts(self):
        """
        This method is used to calculate the amount and taxes of the lines required in the Chilean localization
        electronic documents.
        """
        values = {'price_item': 0, 'total_amount': 0}
        if self.partner_id._l10n_cl_is_delivery_guide_with_no_price():
            return values
        if self.partner_id._l10n_cl_is_delivery_guide_with_sale_order_price() and self.sale_line_id:
            return {
                'price_item': self.sale_line_id.price_unit,
                'discount': self.sale_line_id.discount,
                'total_discount': '{:.0f}'.format(self.sale_line_id.price_unit * self.sale_line_id.product_uom_qty *
                                                  self.sale_line_id.discount / 100),
                'total_amount': self.sale_line_id.price_subtotal
            }
        values.update({
            'price_item': self.product_id.lst_price,
            'total_amount': self.product_id.lst_price * self.product_uom_qty
        })
        return values
