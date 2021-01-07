# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from datetime import datetime
from datetime import time
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)

from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT as DATEFMT

from . import tools_parse

from odoo.exceptions import ValidationError
from odoo.osv import expression

from odoo.addons import decimal_precision as dp

from odoo.tools import float_compare, pycompat

import re

class ProductTemplate(models.Model):
    _inherit = ["product.template"]

    edit_gs1_code = fields.Boolean("Edit GS1-128 code", store=True)
    gs1_128_code = fields.Char("GS1-128 code", store=True)
    
    # @api.model
    # def create(self, vals):
    #     result = super(ProductTemplate, self).create(vals)
        
    #     if 'gs1_128_code' in vals:
    #         result.write({'gs1_128_code': vals['gs1_128_code']})
        
    #     return result

    # def write(self, vals):
    #     if self.env.context.get('finish', False) == True:
    #         return super(ProductTemplate, self).write(vals)
        
    #     if 'gs1_128_code' in vals:
    #         super(ProductTemplate, self).write(vals)
    #         results = self.search([('id', 'in', self._ids)])
    #         for r in results:
    #             if len(r.product_variant_ids) == 1:
    #                 for p in r.product_variant_ids:
    #                     if p.id:
    #                         p.with_context({'finish': True}).write({'gs1_128_code': vals['gs1_128_code']})
            
    #     return super(ProductTemplate, self).write(vals)

class ProductProduct(models.Model):
    _inherit = ["product.product"]
    
    edit_gs1_code = fields.Boolean("Edit GS1-128 code", store=True)
    gs1_128_code = fields.Char("GS1-128 code", store=True)
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            products = self.env['product.product']
            
            result = tools_parse.parse_gs1_128(name)
            p_barcode = ""
            found_01 = False
            found_10 = False
            found_17 = False
            found_21 = False
            for r in result:
                if r['code'] == '01':
                    found_01 = True
                    p_barcode = r['data']
                elif r['code'] == '10':
                    found_10 = True
                elif r['code'] == '17':
                    found_17 = True
                elif r['code'] == '21':
                    found_21 = True
                
                if (found_01 and found_10 and found_17) or (found_01 and found_21):
                    product = self.env['product.product'].search([('barcode', '=', p_barcode)])
        
                    if product:
                        product.write({'gs1_128_code': name})
                    name = p_barcode
                    break
                
            if operator in positive_operators:
                products = self.search([('default_code', '=', name)] + args, limit=limit)
                if not products:
                    products = self.search([('barcode', '=', name)] + args, limit=limit)
            if not products and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                products = self.search(args + [('default_code', operator, name)], limit=limit)
                if not limit or len(products) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(products)) if limit else False
                    products += self.search(args + [('name', operator, name), ('id', 'not in', products.ids)], limit=limit2)
            elif not products and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR([
                    ['&', ('default_code', operator, name), ('name', operator, name)],
                    ['&', ('default_code', '=', False), ('name', operator, name)],
                ])
                domain = expression.AND([args, domain])
                products = self.search(domain, limit=limit)
            if not products and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    products = self.search([('default_code', '=', res.group(2))] + args, limit=limit)
            # still no results, partner in context: search on supplier info as last hope to find something
            if not products and self._context.get('partner_id'):
                suppliers = self.env['product.supplierinfo'].search([
                    ('name', '=', self._context.get('partner_id')),
                    '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)])
                if suppliers:
                    products = self.search([('product_tmpl_id.seller_ids', 'in', suppliers.ids)], limit=limit)
        else:
            products = self.search(args, limit=limit)
        return products.name_get()
    
    # @api.model
    # def create(self, vals):
    #     result = super(ProductProduct, self).create(vals)
        
    #     if 'gs1_128_code' in vals:
    #         result.write({'gs1_128_code': vals['gs1_128_code']})
        
    #     return result
    
    # def write(self, vals):
    #     if 'gs1_128_code' in vals:
    #         result = tools_parse.parse_gs1_128(vals['gs1_128_code'])
    #         for r in result:
    #             if r['code'] == '01':
    #                 vals.update({'barcode': r['data']})
    #             elif r['code'] == '17':
    #                 lote = [item for item in result if item["code"] == "10"]
    #                 if len(lote) > 0:
    #                     lote = lote[0]
    #                     stock_production_lot = self.env['stock.production.lot'].search([('name','=ilike',lote['data'].upper()),('product_id','=',self.id)])
    #                     if len(stock_production_lot) == 0:
    #                         stock_production_lot = self.env['stock.production.lot'].create({'name': lote['data'].upper(), 'product_id': self.id})
                        
    #                     if r['data'].endswith('00'):
    #                         date = (datetime.strptime(r['data'][:4], "%y%m") +
    #                                 relativedelta(months=1) - relativedelta(days=1))
    #                     else:
    #                         date = datetime.strptime(r['data'], '%y%m%d')
                            
    #                     if len(stock_production_lot) > 0:
    #                         date = datetime.combine(date, time(12, 00))
    #                         date_result = date.strftime(DATEFMT)
    #                         stock_production_lot.write({'use_date': date_result,
    #                                             'life_date': date_result,
    #                                             'removal_date': date_result,
    #                                             'alert_date': date_result,})
                                                                                            
    #             elif r['code'] == '10' or r['code'] == '21':
    #                 if r['code'] == '10':
    #                     vals.update({'tracking': 'lot'})
    #                 elif r['code'] == '21':
    #                     vals.update({'tracking': 'serial'})
    #                 stock_production_lot = self.env['stock.production.lot'].search([('name','=ilike',r['data'].upper()),('product_id','=',self.id)])
    #                 if len(stock_production_lot) == 0:
    #                     self.env['stock.production.lot'].create({'name': r['data'].upper(), 'product_id': self.id})
            
    #     return super(ProductProduct, self).write(vals)
