# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.translate import _


class SO(models.Model):
    _inherit = 'sale.order'

    referencia_ids = fields.Char(string='referencia_ids')
    referencias = fields.One2many(
        'l10n_cl.account.invoice.reference',
        'so_id',
        string="Referencias de documento"
    )
    as_reference= fields.Char('Referencia/Descripción')

    def _prepare_invoice(self):
        vals = super(SO, self)._prepare_invoice()
        if self.referencias:
            vals['referencias'] = []
            for ref in self.referencias:
                vals['referencias'].append(
                    (0, 0, {
                        'origin_doc_number': ref.origin_doc_number,
                        'l10n_cl_reference_doc_type_selection': ref.l10n_cl_reference_doc_type_selection,
                        'reason': ref.reason,
                        'date': ref.date,
                    })
                )
        return vals

    @api.onchange('referencias')
    @api.depends('referencias')
    def gte_refrencia(self):
        if self.referencias:
            self.as_reference = self.referencias[0].origin_doc_number
            self.client_order_ref = self.referencias[0].origin_doc_number


    def action_confirm(self):
        vals = super(SO, self).action_confirm()
        #Por Cada Guía
        for do_pick in self.picking_ids:
        #     #Cada Referencia
        #     if self.referencias:
        #         for ref in self.referencias:
        #             data = {
        #                     'origin_doc_number': ref.origin_doc_number,
        #                     'l10n_cl_reference_doc_type_selection': ref.l10n_cl_reference_doc_type_selection,
        #                     'date': ref.date,
        #                     'stock_picking_id': do_pick.id
        #                     } 
        #             self.env['stock.picking.referencias'].create(data)
        #     #Agregamos una Nota a cada Guía
            do_pick.write({'note': self.note})
        return vals


