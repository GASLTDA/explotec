from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    partner_ids = fields.Many2many('res.partner', string='Related Partners')

    @api.model
    def _find_company_from_partner(self, partner_id):
        company = self.sudo().search(['|',('partner_id', '=', partner_id),('partner_ids', 'in', partner_id)], limit=1)
        return company or False
