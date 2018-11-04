from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    bank_info = fields.Text(string="Bank Info.")