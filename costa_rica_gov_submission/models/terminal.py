from odoo import fields, models, api

class terminal(models.Model):
    _name = 'terminal'

    name = fields.Char('Terminal', required=True, max=5)
