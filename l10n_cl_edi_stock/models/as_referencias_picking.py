# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.translate import _


class PosOrder(models.Model):
    _inherit = 'l10n_cl.account.invoice.reference'

    picking_id = fields.Many2one(
            'stock.picking',
            ondelete='cascade',
            index=True,
            copy=False,
            string="Documento",
        )
