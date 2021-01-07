# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from . import tools_parse

class StockInventory(models.Model):
    _name = 'stock.inventory'
    _inherit = ['stock.inventory', 'barcodes.barcode_events_mixin']

    scan_location_id = fields.Many2one('stock.location', 'Scanned Location', store=False)

    def on_barcode_scanned(self, barcode):
        
        result = tools_parse.parse_gs1_128(barcode)
        p_barcode = ""
        found = False
        for r in result:
            if r['code'] == '01':
                p_barcode = r['data']
                found = True
        if not found:
            p_barcode = barcode
        
        product = self.env['product.product'].search([('barcode', '=', p_barcode)])
        
        if product:
            if found:
                product.write({'gs1_128_code': barcode})
            self._add_product(product)
            return

        product_packaging = self.env['product.packaging'].search([('barcode', '=', barcode)])
        if product_packaging.product_id:
            self._add_product(product_packaging.product_id, product_packaging.qty)
            return

        location = self.env['stock.location'].search([('barcode', '=', barcode)])
        if location:
            self.scan_location_id = location[0]
            return
