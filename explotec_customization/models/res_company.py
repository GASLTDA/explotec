from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    product_sequence = fields.Many2one('ir.sequence')
    customer_supplier_sequence = fields.Many2one('ir.sequence')