# -*- coding: utf-8 -*-
import base64

import os

from unittest.mock import patch

import logging

from odoo.addons.stock.tests.common import TestStockCommon

from odoo import fields
from odoo.tools import misc, relativedelta

_logger = logging.getLogger(__name__)


class TestL10nClEdiStock(TestStockCommon):
    @classmethod
    def setUpClass(cls):
        super(TestL10nClEdiStock, cls).setUpClass()

    def setUp(cls):
        cls.company = cls.env['res.company'].create({
            'country_id': cls.env.ref('base.cl').id,
            'currency_id': cls.env.ref('base.CLP').id,
            'name': 'Blanco Martin & Asociados EIRL',
            'street': 'Apoquindo 6410',
            'city': 'Les Condes',
            'phone': '+1 (650) 691-3277 ',
            'l10n_cl_dte_service_provider': 'SIITEST',
            'l10n_cl_dte_resolution_number': 0,
            'l10n_cl_dte_resolution_date': '2019-10-20',
            'l10n_cl_dte_email': 'info@bmya.cl',
            'l10n_cl_sii_regional_office': 'ur_SaC',
            'l10n_cl_company_activity_ids': [(6, 0, [cls.env.ref('l10n_cl_edi.eco_new_acti_620200').id])],
            'extract_show_ocr_option_selection': 'no_send',
        })
        cls.company.partner_id.write({
            'l10n_cl_sii_taxpayer_type': '1',
            'vat': 'CL762012243',
            'l10n_cl_activity_description': 'activity_test',
        })
        cls.certificate = cls.env['l10n_cl.certificate'].sudo().create({
            'signature_filename': 'Test',
            'subject_serial_number': '23841194-7',
            'signature_pass_phrase': 'asadadad',
            'private_key': misc.file_open(os.path.join('l10n_cl_edi_stock', 'tests', 'private_key_test.key')).read(),
            'certificate': misc.file_open(os.path.join('l10n_cl_edi_stock', 'tests', 'cert_test.cert')).read(),
            'cert_expiration': fields.Datetime.now() + relativedelta(years=1),
            'company_id': cls.company.id
        })
        cls.company.write({
            'l10n_cl_certificate_ids': [(4, cls.certificate.id)]
        })

        l10n_latam_document_type_52 = cls.env.ref('l10n_cl_edi_stock.dc_gd_dte')
        l10n_latam_document_type_52.write({'active': True})

        caf_file_template = misc.file_open(os.path.join(
            'l10n_cl_edi_stock', 'tests', 'template', 'caf_file_template.xml')).read()

        caf52_file = caf_file_template.replace('<TD></TD>', '<TD>52</TD>')
        cls.caf52_file = cls.env['l10n_cl.dte.caf'].with_company(cls.company.id).sudo().create({
            'filename': 'FoliosSII7620122435221201910221946.xml',
            'caf_file': base64.b64encode(caf52_file.encode('utf-8')),
            'l10n_latam_document_type_id': l10n_latam_document_type_52.id,
            'status': 'in_use',
        })

    @patch('odoo.addons.l10n_cl_edi_stock.models.stock_picking.Picking._get_next_document_number')
    @patch('odoo.addons.l10n_cl_edi.models.l10n_cl_edi_util.L10nClEdiUtilMixin._get_cl_current_strftime')
    def test_l10n_cl_edi_delivery_stock(self, get_cl_current_strftime, get_next_document_number):
        get_cl_current_strftime.return_value = '2020-10-24T20:00:00'
        get_next_document_number.return_value = 100

        picking = self.PickingObj.with_context(company_id=self.company.id).create({
            'name': 'Test Delivery Guide',
            'picking_type_id': self.picking_type_out,
            'location_id': self.customer_location,
            'location_dest_id': self.stock_location,
        })
        self.MoveObj.create({
            'name': self.productA.name,
            'product_id': self.productA.id,
            'product_uom': self.productA.uom_id.id,
            'product_uom_qty': 10.00,
            'procure_method': 'make_to_stock',
            'location_id': self.customer_location,
            'location_dest_id': self.stock_location,
            'picking_id': picking.id,
        })
        picking.write({'company_id': self.company.id})
        picking.create_delivery_guide()

        self.assertEqual(picking.l10n_cl_dte_status, 'not_sent')

        xml_expected_dte = misc.file_open(os.path.join(
            'l10n_cl_edi_stock', 'tests', 'expected_dtes', 'product_price_list.xml')).read()

        self.assertXmlTreeEqual(
            self.get_xml_tree_from_string(xml_expected_dte.encode()),
            self.get_xml_tree_from_attachment(picking.l10n_cl_sii_send_file)
        )
