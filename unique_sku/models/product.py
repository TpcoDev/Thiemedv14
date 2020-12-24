# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

class ProductChangeQuantity(models.TransientModel):
    _name = "stock.change.product.qty"
    _inherit = ["stock.change.product.qty"]

    def change_product_qty(self):
        """ Changes the Product Quantity by making a Physical Inventory. """
        Inventory = self.env['stock.inventory']
        for wizard in self:
            product = wizard.product_id.with_context(location=wizard.location_id.id, lot_id=wizard.lot_id.id)
            line_data = wizard._action_start_line()

            if wizard.product_id.id and wizard.lot_id.id:
                inventory_filter = 'none'
            elif wizard.product_id.id:
                inventory_filter = 'product'
            else:
                inventory_filter = 'none'

            values = {
                'name': _('INV: %s') % tools.ustr(wizard.product_id.display_name),
                'filter': inventory_filter,
                'product_id': wizard.product_id.id,
                'location_id': wizard.location_id.id,
                'lot_id': wizard.lot_id.id,
                'line_ids': [(0, 0, line_data)],
            }

            if 'assign_custom_date' in self.env.context:
                values.update({'date': '03-30-2019 12:00:01'})

            inventory = Inventory.create(values)
            inventory.action_done()
        return {'type': 'ir.actions.act_window_close'}

class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product"]

    _sql_constraints = [
        ('barcode_uniq', 'Check(1=1)', "Un código de barra, sólo puede sera asignado a un producto !"),
        #('barcode_uniq', 'unique(barcode)', "Un código de barra, sólo puede sera asignado a un producto !"),
    ]

class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template"]

    _sql_constraints = [
        ('default_code_uniq', 'unique(default_code)', "Un código de referencia interna, sólo puede sera asignado a un producto !"),
    ]
