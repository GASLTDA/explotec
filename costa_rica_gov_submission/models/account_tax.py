from odoo import models, fields

class AccountTax(models.Model):
    _inherit='account.tax'

    tax_code = fields.Selection([
        ('01','General sales tax'),
        ('02','Selective Consumer Tax'),
        ('03','Single tax on fuels'),
        ('04','specific tax Alcoholic Beverage'),
        ('05','Specific tax on alcoholic beverages packaged without content and toilet soaps'),
        ('06','Tax on Products Snuff'),
        ('07','Service'),
        ('12','Specific tax Cement'),
        ('98','Others'),
        ('08','exceptions Diplomats General Sales Tax'),
        ('09','General Sales Tax unauthorized purchases'),
        ('10','General sales tax Public institutions and other bodies'),
        ('11','Selective Consumer Tax unauthorized purchases'),
        ('99','Others'),
    ])

    tax_exemption_code = fields.Selection([
        ('01','Compras autorizadas'),
        ('02','Ventas exentas a diplomáticos'),
        ('03','Orden de compra (Instituciones Públicas y otros organismos)'),
        ('04','Exenciones Dirección General de Hacienda'),
        ('05','Zonas Francas'),
        ('99','Otros'),
    ])

    tax_exemption_number = fields.Char()
    tax_exemption_issuer_number = fields.Char()
    tax_exemption_date_time = fields.Datetime()
    tax_authorized_amount = fields.Float()
    tax_authorized_percentage = fields.Float()

