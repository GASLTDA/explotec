import string

from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    fax_no = fields.Char('Fax No.', size=20)
    fax_code = fields.Char('Fax Code.', size=3)
    province_id = fields.Many2one('province', string='Province', placeholder='Province')
    canton_id = fields.Many2one('canton', string='Canton', placeholder='Canton',domain="[('province_id','=',province_id)]")
    district_id = fields.Many2one('district', string='District', placeholder='District',domain="[('canton_id','=',canton_id)]")
    locality_id = fields.Many2one('locality', string='Locality', placeholder='Locality',domain="[('district_id','=',district_id)]")
    phone = fields.Char('Phone', size=20)
    phone_code = fields.Char('Phone Code', size=3)
    tipo = fields.Selection([('01','Cédula Física'),('02','Cédula Jurídica'),('03','DIMEX'),('04','NITE')],default='02')

    # @api.onchange('name')
    # def onchange_name(self):
    #     all_normal_characters = string.ascii_letters
    #     for char in self.name:
    #         if char not in all_normal_characters and char != ' ':
    #             name = self.name
    #             self.name = name.replace(char,'')