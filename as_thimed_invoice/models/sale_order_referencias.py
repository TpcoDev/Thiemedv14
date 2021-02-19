# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.translate import _


class PosOrder(models.Model):
    _inherit = 'l10n_cl.account.invoice.reference'

    so_id = fields.Many2one(
            'sale.order',
            ondelete='cascade',
            index=True,
            copy=False,
            string="Documento",
        )

    @api.onchange('origin_doc_number')
    @api.depends('origin_doc_number')
    def gte_refrencia(self):
        if self._origin.so_id:
            self._origin.so_id.as_reference = self._origin.origin_doc_number




