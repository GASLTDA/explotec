from odoo import fields, api, models

class Province(models.Model):
    _name = 'province'

    name = fields.Char('Province', required=True)
    code = fields.Char('Code', required=True)

class Canton(models.Model):
    _name = 'canton'

    name = fields.Char('Canton', required=True)
    code = fields.Char('Code', required=True)
    province_id = fields.Many2one('province', required=True)

class District(models.Model):
    _name = 'district'

    name = fields.Char('District', required=True)
    code = fields.Char('Code', required=True)
    canton_id = fields.Many2one('canton', required=True)

class Locality(models.Model):
    _name = 'locality'

    name = fields.Char('Locality', required=True)
    code = fields.Char('Code', required=True)
    district_id = fields.Many2one('district', required=True)