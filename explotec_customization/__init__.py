from . import models
from odoo import api, SUPERUSER_ID

def _auto_install_data(cr, registry):

    env = api.Environment(cr, SUPERUSER_ID, {})
    product_ids = env['product.template'].search([('default_code','=', False)])
    for product in product_ids:
        product.write({
            'default_code': env['ir.sequence'].next_by_code('product')
        })

    partner_ids = env['res.partner'].search([('ref','=', False)])
    for partner in partner_ids:
        partner.write({
            'ref': env['ir.sequence'].next_by_code('partner')
        })