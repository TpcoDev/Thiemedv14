# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    analytic_tag_id = fields.Many2one(
        'account.analytic.tag', string="Analytic tag",
        help="Analytic tag associated with the invoice. E.g. DIN1")

    def search_tags(self):
        
        if self.cost_lines:
            raise ValidationError(_("The cost lines were already generated."))

        invoices = self.env['account.move'].search([]).filtered(
            lambda r: self.analytic_tag_id in r.analytic_tag_ids)

        if not invoices:
            raise ValidationError(_(
                "There are no results for this analytic tag."))

        cost_lines = {}
        for invoice_line in invoices.mapped('invoice_line_ids'):
            if invoice_line.product_id.landed_cost_ok:
                cost_lines.update({
                    invoice_line.product_id: cost_lines.get(
                        invoice_line.product_id, 0.0) + invoice_line.price_unit,
                })

        if not cost_lines:
            raise ValidationError(_(
                "No landed cost product was found for this analytic tag."))

        self.write({
            'cost_lines': [(0, 0, {
                'product_id': product.id,
                'name': product.name or '',
                'split_method': product.split_method_landed_cost or 'equal',
                'price_unit': price,
                'account_id': product.property_account_expense_id.id or product.categ_id.property_account_expense_categ_id.id,
                }) for product, price in cost_lines.items()],
        })


    def get_valuation_lines(self):
        """Overwrites the original method to include average in the validation
        of the cost methods."""
        lines = []

        for move in self.mapped('picking_ids').mapped('move_lines'):
            if move.product_id.valuation != 'real_time' or move.product_id.cost_method not in ['fifo', 'average']:
                continue
            vals = {
                'product_id': move.product_id.id,
                'move_id': move.id,
                'quantity': move.product_qty,
                'former_cost': move.product_id.standard_price,
                'weight': move.product_id.weight * move.product_qty,
                'volume': move.product_id.volume * move.product_qty
            }
            lines.append(vals)

        if not lines and self.mapped('picking_ids'):
            raise UserError(_(
                'The selected picking does not contain any move that would be '
                'impacted by landed costs. Landed costs are only possible for '
                'products configured in real time valuation with real price '
                'costing method. Please make sure it is the case, or you '
                'selected the correct picking'))
        return lines


class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    new_cost = fields.Float(
        compute='_compute_new_cost',
        help="Former Cost (Per unit) + Additional Landed Cost / Quantity")

    def _compute_new_cost(self):
        """Computes the new cost amount"""
        for record in self:
            record.new_cost = (
                record.final_cost + record.additional_landed_cost
                / record.quantity)
