# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class L10nLatamDocumentType(models.Model):
    _inherit = 'l10n_latam.document.type'

    internal_type = fields.Selection(selection_add=[('stock_picking', 'Stock Picking')])

    def _is_doc_type_stock_picking(self):
        return self.internal_type == 'stock_picking'

    # def _is_doc_type_voucher(self):
    #     return self.code in ['35', '39', '906', '45', '46', '70', '71','52']

