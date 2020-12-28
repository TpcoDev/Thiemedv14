# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.translate import _


class SO(models.Model):
    _inherit = 'sale.order'


    referencia_ids = fields.One2many(
        'sale.order.referencias',
        'so_id',
        string="Referencias de documento"
    )
    as_reference= fields.Char('Referencia/Descripción')

    def _prepare_invoice(self):
        vals = super(SO, self)._prepare_invoice()
        if self.referencia_ids:
            vals['referencias'] = []
            for ref in self.referencia_ids:
                vals['referencias'].append(
                    (0, 0, {
                        'origen': ref.folio,
                        'sii_referencia_TpoDocRef': ref.sii_referencia_TpoDocRef.id,
                        'motivo': ref.motivo,
                        'fecha_documento': ref.fecha_documento,
                    })
                )
        return vals

    @api.onchange('referencia_ids')
    @api.depends('referencia_ids')
    def gte_refrencia(self):
        if self.referencia_ids:
            self.as_reference = self.referencia_ids[0].folio


    def action_confirm(self):
        vals = super(SO, self).action_confirm()
        #Por Cada Guía
        for do_pick in self.picking_ids:
        #     #Cada Referencia
        #     if self.referencia_ids:
        #         for ref in self.referencia_ids:
        #             data = {
        #                     'origen': ref.folio,
        #                     'sii_referencia_TpoDocRef': ref.sii_referencia_TpoDocRef.id,
        #                     'date': ref.fecha_documento,
        #                     'stock_picking_id': do_pick.id
        #                     } 
        #             self.env['stock.picking.referencias'].create(data)
        #     #Agregamos una Nota a cada Guía
            do_pick.write({'note': self.note})
        return vals


