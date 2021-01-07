# _*_ coding: utf_8 _*_

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import UserError


import logging
_logger = logging.getLogger(__name__)

class stockpicking(models.Model):
    _inherit = "stock.picking"

    maintenance_id = fields.Many2one('maintenance.workorder', string='Mantenimiento')