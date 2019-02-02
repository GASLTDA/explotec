from odoo import models, fields, api

class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_stock = fields.Boolean('Stock', default=False)