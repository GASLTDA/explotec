from odoo import models, fields, api,_

class ResCompany(models.Model):
    _inherit = 'res.company'

    province_id = fields.Many2one('province', string='Province', placeholder='Province')
    canton_id = fields.Many2one('canton', string='Canton', placeholder='Canton',domain="[('province_id','=',province_id)]")
    district_id = fields.Many2one('district', string='District', placeholder='District',domain="[('canton_id','=',canton_id)]")
    locality_id = fields.Many2one('locality', string='Locality', placeholder='Locality',domain="[('district_id','=',district_id)]")
    fax_no = fields.Char('Fax No.', size=20)
    registration_date = fields.Datetime('Registration')
    phone = fields.Char('Phone', size=20)
    phone_code = fields.Char('Phone Code', size=3)

    fax_code = fields.Char('Fax Code.', size=3)

    company_registry = fields.Char(size=13)
    store_branch = fields.Char('Store/Branch No.', size=3)

    access_token = fields.Text()
    url = fields.Char()
    electronic_invoice = fields.Boolean(default=True)
