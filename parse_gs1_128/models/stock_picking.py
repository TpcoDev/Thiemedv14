# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round

import json

from . import tools_parse

import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'barcodes.barcode_events_mixin']

    def get_po_to_split_from_barcode(self, barcode):
        """ Returns the lot wizard's action for the move line matching
        the barcode. This method is intended to be called by the
        `picking_barcode_handler` javascript widget when the user scans
        the barcode of a tracked product.
        """
        
        result = tools_parse.parse_gs1_128(barcode)
        p_barcode = ""
        found = False
        for r in result:
            if r['code'] == '01':
                p_barcode = r['data']
                found = True
        if not found:
            p_barcode = barcode
        
        product_id = self.env['product.product'].search([('barcode', '=', p_barcode)])
        
        if found:
            if product_id:
                product_id.write({'gs1_128_code': barcode})
                
        candidates = self.env['stock.move.line'].search([
            ('picking_id', 'in', self.ids),
            ('product_barcode', '=', barcode),
            ('location_processed', '=', False),
            ('result_package_id', '=', False),
        ])

        action_ctx = dict(self.env.context,
            default_picking_id=self.id,
            serial=self.product_id.tracking == 'serial',
            default_product_id=product_id.id,
            candidates=candidates.ids)
        view_id = self.env.ref('stock_barcode.view_barcode_lot_form').id
        return {
            'name': _('Lot/Serial Number Details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock_barcode.lot',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'context': action_ctx}

    def new_product_scanned(self, barcode):
        # TODO: remove this method in master, it's not used anymore
        
        result = tools_parse.parse_gs1_128(barcode)
        p_barcode = ""
        found = False
        for r in result:
            if r['code'] == '01':
                p_barcode = r['data']
                found = True
        if not found:
            p_barcode = barcode
        
        product_id = self.env['product.product'].search([('barcode', '=', p_barcode)])
        if not product_id or product_id.tracking == 'none':
            return self.on_barcode_scanned(barcode)
        else:
            return self.get_po_to_split_from_barcode(barcode)

    def on_barcode_scanned(self, barcode):
        if not self.picking_type_id.barcode_nomenclature_id:
            # Logic for products
            result = tools_parse.parse_gs1_128(barcode)
            p_barcode = ""
            p_lote = ""
            found = False
            for r in result:
                if r['code'] == '01':
                    p_barcode = r['data']
                    found = True
                if r['code'] == '10':
                    p_lote = r['data']
                if r['code'] == '21':
                    p_lote = r['data']
            if not found:
                p_barcode = barcode
            
            product = self.env['product.product'].search(['|', ('barcode', '=', p_barcode), ('default_code', '=', p_barcode)], limit=1)
            if product:
                if found:
                    product.write({'gs1_128_code': barcode})
                if self._check_product(product, 1.0, p_lote):
                    return

            product_packaging = self.env['product.packaging'].search([('barcode', '=', barcode)], limit=1)
            if product_packaging.product_id:
                if self._check_product(product_packaging.product_id,product_packaging.qty):
                    return

            # Logic for packages in source location
            if self.move_line_ids:
                package_source = self.env['stock.quant.package'].search([('name', '=', barcode), ('location_id', 'child_of', self.location_id.id)], limit=1)
                if package_source:
                    if self._check_source_package(package_source):
                        return

            # Logic for packages in destination location
            package = self.env['stock.quant.package'].search([('name', '=', barcode), '|', ('location_id', '=', False), ('location_id','child_of', self.location_dest_id.id)], limit=1)
            if package:
                if self._check_destination_package(package):
                    return

            # Logic only for destination location
            location = self.env['stock.location'].search(['|', ('name', '=', barcode), ('barcode', '=', barcode)], limit=1)
            if location and location.parent_left < self.location_dest_id.parent_right and location.parent_left >= self.location_dest_id.parent_left:
                if self._check_destination_location(location):
                    return
        else:
            result = tools_parse.parse_gs1_128(barcode)
            p_barcode = ""
            found = False
            for r in result:
                if r['code'] == '01':
                    p_barcode = r['data']
                    found = True
            
            if found:
                product = self.env['product.product'].search(['|', ('barcode', '=', p_barcode), ('default_code', '=', p_barcode)], limit=1)
                if product:
                    product.write({'gs1_128_code': barcode})
                    if self._check_product(product, 1.0, p_lote):
                        return
            
            parsed_result = self.picking_type_id.barcode_nomenclature_id.parse_barcode(barcode)
            if parsed_result['type'] in ['weight', 'product']:
                if parsed_result['type'] == 'weight':
                    product_barcode = parsed_result['base_code']
                    qty = parsed_result['value']
                else: #product
                    product_barcode = parsed_result['code']
                    qty = 1.0
                product = self.env['product.product'].search(['|', ('barcode', '=', product_barcode), ('default_code', '=', product_barcode)], limit=1)
                if product:
                    if self._check_product(product, qty, p_lote):
                        return

            if parsed_result['type'] == 'package':
                if self.move_line_ids:
                    package_source = self.env['stock.quant.package'].search([('name', '=', parsed_result['code']), ('location_id', 'child_of', self.location_id.id)], limit=1)
                    if package_source:
                        if self._check_source_package(package_source):
                            return
                package = self.env['stock.quant.package'].search([('name', '=', parsed_result['code']), '|', ('location_id', '=', False), ('location_id','child_of', self.location_dest_id.id)], limit=1)
                if package:
                    if self._check_destination_package(package):
                        return

            if parsed_result['type'] == 'location':
                location = self.env['stock.location'].search(['|', ('name', '=', parsed_result['code']), ('barcode', '=', parsed_result['code'])], limit=1)
                if location and location.parent_left < self.location_dest_id.parent_right and location.parent_left >= self.location_dest_id.parent_left:
                    if self._check_destination_location(location):
                        return

            product_packaging = self.env['product.packaging'].search([('barcode', '=', parsed_result['code'])], limit=1)
            if product_packaging.product_id:
                if self._check_product(product_packaging.product_id,product_packaging.qty, p_lote):
                    return

        return {'warning': {
            'title': _('Wrong barcode'),
            'message': _('The barcode "%(barcode)s" doesn\'t correspond to a proper product, package or location.') % {'barcode': barcode}
        }}
        
    def _check_product(self, product, qty=1.0, lote=""):
        """ This method is called when the user scans a product. Its goal
        is to find a candidate move line (or create one, if necessary)
        and process it by incrementing its `qty_done` field with the
        `qty` parameter.
        """
        # Get back the move line to increase. If multiple are found, chose
        # arbitrary the first one. Filter out the ones processed by
        # `_check_location` and the ones already having a # destination
        # package.
        # Revisar esto. CESAR CORDERO
        #Inicio agregado nuevo
        if lote and len(lote) > 0:
            stock_production_lot = self.env['stock.production.lot'].search([('name','=ilike',lote.upper()),('product_id','=',product.id)])
            if len(stock_production_lot) == 0:
                stock_production_lot = self.env['stock.production.lot'].create({'name': lote.upper(), 'product_id': product.id})

            corresponding_ml = self.move_line_ids.filtered(lambda ml: ml.product_id.id == product.id and not ml.result_package_id and not ml.location_processed and (str(ml.lot_id.name).upper() == lote.upper() or str(ml.lot_name).upper() == lote.upper()))
            corresponding_ml = corresponding_ml[0] if corresponding_ml else False
        else:
            corresponding_ml = self.move_line_ids.filtered(lambda ml: ml.product_id.id == product.id and not ml.result_package_id and not ml.location_processed and not ml.lots_visible)
            corresponding_ml = corresponding_ml[0] if corresponding_ml else False
        #Fin agregado nuevo
        #Debería estar así:
        """
        #corresponding_ml = self.move_line_ids.filtered(lambda ml: ml.product_id.id == product.id and not ml.result_package_id and not ml.location_processed and not ml.lots_visible)
        #corresponding_ml = corresponding_ml[0] if corresponding_ml else False
        """

        if corresponding_ml:
            corresponding_ml.qty_done += qty
        else:
            # If a candidate is not found, we create one here. If the move
            # line we add here is linked to a tracked product, we don't
            # set a `qty_done`: a next scan of this product will open the
            # lots wizard.
            picking_type_lots = (self.picking_type_id.use_create_lots or self.picking_type_id.use_existing_lots)
            
            values = {
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'qty_done': 1.0, #(product.tracking == 'none' and picking_type_lots) and qty or 0.0,
                'product_uom_qty': 0.0,
                'date': fields.datetime.now(),
            }
            
            if lote and len(lote) > 0:
                lote = self.env['stock.production.lot'].search([('name', '=ilike', lote.upper()), ('product_id', '=', product.id)])
            
                if lote:
                    values.update({'lot_id': lote.id, 'lot_name': lote.name})
                    
            self.move_line_ids += self.move_line_ids.new(values)
            
        return True

    @api.model
    def create(self, vals):
        result = super(StockPicking, self).create(vals)
        
        #if 'move_line_ids' in vals:
        #    record = self.search([('id', '=', result.id)])
        #    #record.change_move_line_ids()
        
        return result
        
    def write(self, vals):
        result = super(StockPicking, self).write(vals)
        
        #if 'move_line_ids' in vals:
        #    for s in self:
        #        record = self.search([('id', '=', s.id)])
        #        #record.change_move_line_ids()
        
        return result
    
    """
    def change_move_line_ids(self):
        all_records = []
        records_getted = []
        for record in self.move_line_ids:
            for record_self in self.move_line_ids:
                if record.id != record_self.id:
                    if record.product_id.id == record_self.product_id.id:
                        if record.lot_id.id == record_self.lot_id.id:
                            record.write({'qty_done': record.qty_done + record_self.qty_done})
                            
                            record_self.write({'qty_done': 0.0})
                        if not record_self.lot_id.id and record.lot_id.id:
                            record.write({'qty_done': record.qty_done + record_self.qty_done})
                            
                            record_self.write({'qty_done': 0.0})
                        if record_self.lot_id.id and not record.lot_id.id:
                            record_self.write({'qty_done': record.qty_done + record_self.qty_done})
                            
                            record.write({'qty_done': 0.0})
                        #if not record.lot_id.id and not record_self.lot_id.id:
                        #    record.write({'qty_done': record.qty_done + record_self.qty_done})
                        #    
                        #    record_self.write({'qty_done': 0.0})
        
        for record in self.move_line_ids:
            if record.qty_done == 0:
               record.unlink() 
        return all_records
    """
