# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking"]
    
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Etiquetas analíticas')
    
    @api.model
    def get_products_invoice(self):
        account_invs = self.env['account.move'].search([('analytic_tag_ids', 'in', self.analytic_tag_ids.ids)])
        
        for i in self.move_lines:
            if not i.pedido:
                i.product_uom_qty = 0
        
        new_lines = self.env['stock.move']
        for a_inv in account_invs:
            for i_l_id in a_inv.invoice_line_ids:
                found = False
                for i in self.move_lines:
                    if i_l_id.product_id.id == i.product_id.id and not i.pedido:
                        i.product_uom_qty += i_l_id.quantity
                        found = True
                        break
                        
                if not found:
                    data = {
                                'product_id': i_l_id.product_id.id,
                                'name': i_l_id.product_id.name,
                                'product_uom': i_l_id.uom_id.id,
                                'location_dest_id': self.location_dest_id.id,
                                'location_id': self.location_id.id,
                                'product_uom_qty': i_l_id.quantity,
                                'pedido': False
                            }
                    new_line = new_lines.new(data)
                    new_lines += new_line
        
        self.move_lines += new_lines
        
        return True

class StockMove(models.Model):
    _name = "stock.move"
    _inherit = ["stock.move"]
    
    pedido = fields.Selection([
        ('pedido', 'Pedido'),
        ('aceptado', 'Aceptado'),
        ('rechazado', 'Rechazado'),],
                    string='Aceptado?')

class AccountInvoice(models.Model):
    _name = "account.move"
    _inherit = ["account.move"]
    
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Etiquetas analíticas')

    #@api.onchange("whin_id")
    #def onchange_whin_id(self):
    #    if self.whin_id:
    #        self.analytic_tag_ids = self.whin_id.analytic_tag_ids
            
    @api.onchange("analytic_tag_ids")
    def onchange_analytic_tag_ids(self):
        for i in self.invoice_line_ids:
            i.analytic_tag_ids = self.analytic_tag_ids

class AccountInvoiceLine(models.Model):
    _name = "account.move.line"
    _inherit = "account.move.line"
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        domain = {}
        if not self.invoice_id:
            return

        part = self.invoice_id.partner_id
        fpos = self.invoice_id.fiscal_position_id
        company = self.invoice_id.company_id
        currency = self.invoice_id.currency_id
        type = self.invoice_id.type
        self.analytic_tag_ids = self.invoice_id.analytic_tag_ids

        if not part:
            warning = {
                    'title': _('Warning!'),
                    'message': _('You must first select a partner!'),
                }
            return {'warning': warning}

        if not self.product_id:
            if type not in ('in_invoice', 'in_refund'):
                self.price_unit = 0.0
            domain['uom_id'] = []
        else:
            if part.lang:
                product = self.product_id.with_context(lang=part.lang)
            else:
                product = self.product_id

            self.name = product.partner_ref
            account = self.get_invoice_line_account(type, product, fpos, company)
            if account:
                self.account_id = account.id
            self._set_taxes()

            if type in ('in_invoice', 'in_refund'):
                if product.description_purchase:
                    self.name += '\n' + product.description_purchase
            else:
                if product.description_sale:
                    self.name += '\n' + product.description_sale

            if not self.uom_id or product.uom_id.category_id.id != self.uom_id.category_id.id:
                self.uom_id = product.uom_id.id
            domain['uom_id'] = [('category_id', '=', product.uom_id.category_id.id)]

            if company and currency:

                if self.uom_id and self.uom_id.id != product.uom_id.id:
                    self.price_unit = product.uom_id._compute_price(self.price_unit, self.uom_id)
        return {'domain': domain}
