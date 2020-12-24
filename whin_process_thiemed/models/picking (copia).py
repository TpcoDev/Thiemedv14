# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from datetime import datetime

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _name = "account.move"
    _inherit = ["account.move"]

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None, tipo_nota=61, mode='1'):
        values = super(AccountInvoice, self)._prepare_refund(invoice, date_invoice, date, description, journal_id)
        document_type = self.env['account.journal.sii_document_class'].search(
                [
                    ('sii_document_class_id.sii_code','=', tipo_nota),
                    ('journal_id','=', invoice.journal_id.id),
                ],
                limit=1,
            )
        if invoice.type == 'out_invoice':
            type = 'out_refund'
        elif invoice.type == 'out_refund':
            type = 'out_invoice'
        elif invoice.type == 'in_invoice':
            type = 'in_refund'
        elif invoice.type == 'in_refund':
            type = 'in_invoice'
            
        referencias = [[0,0, {
                'origen': int(invoice.sii_document_number or invoice.reference),
                'sii_referencia_TpoDocRef': invoice.sii_document_class_id.id,
                'sii_referencia_CodRef': mode,
                'motivo': description,
                'fecha_documento': invoice.date_invoice
            }]]
            
        if invoice.sale_id:
            s_p_record_ids = self.env['stock.picking'].search([('origin', '=', invoice.sale_id.name), ('state', '=', 'done')])
            for s_p_id in s_p_record_ids:
                if s_p_id.name[:3].upper() == "GDE":
                    g_d_sii_id = self.env['sii.document_class'].search([('name', '=', 'Guía de Despacho Electrónica')])
                    referencias.append([0,0, {
                                'origen': s_p_id.name[3:],
                                'sii_referencia_TpoDocRef': g_d_sii_id.id,
                                'sii_referencia_CodRef': mode,
                                'motivo': "Guía de Despacho: " + s_p_id.name,
                                'fecha_documento': s_p_id.scheduled_date
                            }])

        values.update({
                'type': type,
                'journal_document_class_id': document_type.id,
                'referencias': referencias,
            })
        return values

class SaleAdvancePaymentInv(models.TransientModel):
    _name = "sale.advance.payment.inv"
    _inherit = ["sale.advance.payment.inv"]
    
    def _create_invoice(self, order, so_line, amount):
        inv_obj = self.env['account.move']
        ir_property_obj = self.env['ir.property']

        account_id = False
        if self.product_id.id:
            account_id = self.product_id.property_account_income_id.id or self.product_id.categ_id.property_account_income_categ_id.id
        if not account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
        if not account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (self.product_id.name,))

        if self.amount <= 0.00:
            raise UserError(_('The value of the down payment amount must be positive.'))
        context = {'lang': order.partner_id.lang}
        if self.advance_payment_method == 'percentage':
            amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount,)
        else:
            amount = self.amount
            name = _('Down Payment')
        del context
        taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
        if order.fiscal_position_id and taxes:
            tax_ids = order.fiscal_position_id.map_tax(taxes).ids
        else:
            tax_ids = taxes.ids
            
        s_p_record_ids = self.env['stock.picking'].search([('origin', '=', order.name), ('state', '=', 'done')])
        
        values = {
            'name': order.client_order_ref or order.name,
            'origin': order.name,
            'type': 'out_invoice',
            'reference': False,
            'account_id': order.partner_id.property_account_receivable_id.id,
            'partner_id': order.partner_invoice_id.id,
            'partner_shipping_id': order.partner_shipping_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'origin': order.name,
                'account_id': account_id,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id,
                'sale_line_ids': [(6, 0, [so_line.id])],
                'invoice_line_tax_ids': [(6, 0, tax_ids)],
                'account_analytic_id': order.analytic_account_id.id or False,
            })],
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_term_id': order.payment_term_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'team_id': order.team_id.id,
            'user_id': order.user_id.id,
            'comment': order.note,
        }
        
        if order.name.upper().startswith('SO'):
            referencias = []
            for ref in order.referencia_ids:
                referencias.append(
                    (0, 0, {
                        'origen': ref.folio,
                        'sii_referencia_TpoDocRef': ref.sii_referencia_TpoDocRef.id,
                        'motivo': ref.motivo,
                        'fecha_documento': ref.fecha_documento,
                    })
                )
            
            for s_p_id in s_p_record_ids:
                if s_p_id.name[:3].upper() == "GDE":
                    g_d_sii_id = self.env['sii.document_class'].search([('name', '=', 'Guía de Despacho Electrónica')])
                    referencias.append(
                        (0, 0, {
                            'origen': s_p_id.name[3:],
                            'sii_referencia_TpoDocRef': g_d_sii_id.id,
                            'motivo': "Guía de Despacho: " + s_p_id.name,
                            'fecha_documento': s_p_id.scheduled_date,
                        })
                    )
            
                    values.update({'picking_id': s_p_id.id, 'sale_id': order.id, 'referencias': referencias})
            
            #s_i_t_id = self.env['stock.immediate.transfer'].create({'pick_ids': [(6,0,[s_p_id.id])]})
            #s_p_id.process()

        invoice = inv_obj.create(values)
        invoice.compute_taxes()
        invoice.message_post_with_view('mail.message_origin_link',
                    values={'self': invoice, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return invoice

class SO(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        vals = super(SO, self)._prepare_invoice()
        
        s_p_record_ids = self.env['stock.picking'].search([('origin', '=', self.name), ('state', '=', 'done')])
        
        vals['referencias'] = []
        if self.referencia_ids:
            for ref in self.referencia_ids:
                vals['referencias'].append(
                    (0, 0, {
                        'origen': ref.folio,
                        'sii_referencia_TpoDocRef': ref.sii_referencia_TpoDocRef.id,
                        'motivo': ref.motivo,
                        'fecha_documento': ref.fecha_documento,
                    })
                )
        for s_p_id in s_p_record_ids:
            if s_p_id.name[:3].upper() == "GDE":
                g_d_sii_id = self.env['sii.document_class'].search([('name', '=', 'Guía de Despacho Electrónica')])
                vals['referencias'].append(
                    (0, 0, {
                        'origen': s_p_id.name[3:],
                        'sii_referencia_TpoDocRef': g_d_sii_id.id,
                        'motivo': "Guía de Despacho: " + s_p_id.name,
                        'fecha_documento': s_p_id.scheduled_date,
                    })
                )
            
        return vals

    def action_confirm(self):
        vals = super(SO, self).action_confirm()
        #Por Cada Guía
        for do_pick in self.picking_ids:
            #Cada Referencia
            if self.referencia_ids:
                for ref in self.referencia_ids:
                    data = {
                            'origen': ref.folio,
                            'sii_referencia_TpoDocRef': ref.sii_referencia_TpoDocRef.id,
                            'date': ref.fecha_documento,
                            'stock_picking_id': do_pick.id,
                            } 
                    self.env['stock.picking.referencias'].create(data)
            #Agregamos una Nota a cada Guía
            do_pick.write({'note': self.note})
        return vals

class account_invoice(models.Model):
    _inherit  =  'account.move'

    picking_id = fields.Many2one('stock.picking','Picking')
    sale_id  =  fields.Many2one('sale.order', 'Sale Origin')
    pur_id   =  fields.Many2one('purchase.order', 'Purchase Origin')
    sale_count = fields.Float('Sales Count')

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id

        new_lines = self.env['account.move.line']
        for line in self.purchase_id.order_line:
            # Load a PO line only once
            if line in self.invoice_line_ids.mapped('purchase_line_id') and line.product_qty <=0:
                continue
            data = self._prepare_invoice_line_from_po_line(line)
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.invoice_line_ids += new_lines
        self.purchase_id = False

        return {}

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('state')
    def _get_invoiced(self):
        for order in self:
            invoice_ids = self.env['account.move'].search([('picking_id','=',order.id)])
            order.invoice_count = len(invoice_ids)

    invoice_count = fields.Integer(string='# of Invoices', compute='_get_invoiced',  )
