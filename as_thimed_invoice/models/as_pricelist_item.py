from odoo import api, fields, models
    
class product_pricelist_item(models.Model):
    _inherit = "product.pricelist.item"
    
    def _onchange_product_tmpl(self):
        for rec in self:
            rec.default_code_item = ''
            if rec.product_tmpl_id:
                rec.default_code_item=rec.product_tmpl_id.default_code
            if rec.product_id: 
                rec.default_code_item=rec.product_id.default_code

    default_code_item= fields.Char('Referencia Interna',compute='_onchange_product_tmpl')

