from odoo import models, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        if 'default_code' in vals and vals['default_code'] == False:
            if vals['company_id'] != False:
                company_id = self.env['res.company'].sudo().browse(vals['company_id'])
                vals['default_code'] = self.env['ir.sequence'].next_by_code(company_id.product_sequence.code)
            else:
                vals['default_code'] = self.env['ir.sequence'].next_by_code('product')

        elif 'default_code' in vals and vals['default_code'] != False:
            if self.env['product.template'].search([('default_code','=', vals['default_code'])], limit=1).id:
                raise UserError(_(
                    'Reference number is already present'
                ))
        return super(ProductTemplate, self).create(vals)
