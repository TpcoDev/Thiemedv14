# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.translate import _


class SOR(models.Model):
    _name = 'sale.order.referencias'

    fecha_documento = fields.Date(
            string="Fecha Documento",
            required=True,
        )
    folio = fields.Char(
            string="Folio Referencia",
        )
    sii_referencia_TpoDocRef = fields.Many2one(
            'sii.document_class',
            string="Tipo de Documento SII",
        )
    motivo = fields.Char(
            string="Motivo",
        )
    so_id = fields.Many2one(
            'sale.order',
            ondelete='cascade',
            index=True,
            copy=False,
            string="Documento",
        )

class sii_document_class(models.Model):
    _name = 'sii.document_class'
    _description = 'SII Document Class'

    name = fields.Char(
        'Name', size=120)
    doc_code_prefix = fields.Char(
        'Document Code Prefix', help="Prefix for Documents Codes on Invoices \
        and Account Moves. For eg. 'FAC' will build 'FAC 00001' Document Number")
    code_template = fields.Char(
        'Code Template for Journal')
    sii_code = fields.Integer(
        'SII Code', required=True)
    document_letter_id = fields.Many2one(
        'sii.document_letter', 'Document Letter')
    report_name = fields.Char(
        'Name on Reports',
        help='Name that will be printed in reports, for example "CREDIT NOTE"')
    document_type = fields.Selection(
        [
            ('invoice', 'Invoices'),
            ('invoice_in', 'Purchase Invoices'),
            ('debit_note', 'Debit Notes'),
            ('credit_note', 'Credit Notes'),
            ('stock_picking', 'Stock Picking'),
            ('other_document', 'Other Documents')
        ],
        string='Document Type',
        help='It defines some behaviours on automatic journal selection and\
        in menus where it is shown.')
    active = fields.Boolean(
        'Active', default=True)
    dte = fields.Boolean(
        'DTE', required=True)
    use_prefix = fields.Boolean(
            string="Usar Prefix en las referencias DTE",
            default=False,
        )