from odoo import models, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        if 'ref' in vals and vals['ref'] == False:
            if vals['company_id'] != False:
                company_id = self.env['res.company'].sudo().browse(vals['company_id'])
                vals['ref'] = self.env['ir.sequence'].next_by_code(company_id.customer_supplier_sequence.code)
            else:
                vals['ref'] = self.env['ir.sequence'].next_by_code('partner')
        elif 'ref' in vals and vals['ref'] != False:
            if self.env['res.partner'].search([('ref','=', vals['ref'])], limit=1).id:
                raise UserError(_(
                    'Reference number is already present'
                ))

        return super(ResPartner, self).create(vals)