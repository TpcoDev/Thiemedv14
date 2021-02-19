# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.translate import _


class SO(models.Model):
    _inherit = 'account.move'


    referencias = fields.One2many(
        'l10n_cl.account.invoice.reference',
        'move_id',
        string="Referencias de documento"
    )
    as_reference= fields.Char('Referencia/Descripción')

    @api.onchange('referencias')
    @api.depends('referencias')
    def gte_refrencia(self):
        if self.referencias:
            self.as_reference = self.referencias[0].origin_doc_number
            self.ref = self.referencias[0].origin_doc_number


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _create_invoice(self, order, so_line, amount):
        res = super(SaleAdvancePaymentInv,self)._create_invoice(order, so_line, amount)
        vals = []
        if order.referencias:
            for ref in order.referencias:
                vals.append(ref.id)
            res.write({'referencias':vals,'as_reference':order.as_reference})
      
        return res
