# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.translate import _


class SO(models.Model):
    _inherit = 'sale.order'   
    
    def action_confirm(self):
        res = super(SO, self).action_confirm()
        for pick in self.picking_ids:
            for sale_ref in self.referencias:
                sale_ref.picking_id = pick.id
        return res