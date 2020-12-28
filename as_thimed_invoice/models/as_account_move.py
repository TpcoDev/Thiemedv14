# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.translate import _


class SO(models.Model):
    _inherit = 'account.move'


    referencias = fields.One2many(
        'sale.order.referencias',
        'mv_id',
        string="Referencias de documento"
    )
    as_reference= fields.Char('Referencia/Descripción')

    @api.onchange('referencia_ids')
    @api.depends('referencia_ids')
    def gte_refrencia(self):
        if self.referencias:
            self.as_reference = self.referencias[0].folio


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _create_invoice(self, order, so_line, amount):
        res = super(SaleAdvancePaymentInv,self)._create_invoice(order, so_line, amount)
        vals = []
        if order.referencia_ids:
            for ref in order.referencia_ids:
                vals.append(ref.id)
            res.write({'referencias':vals,'as_reference':order.as_reference})
      
        return res
