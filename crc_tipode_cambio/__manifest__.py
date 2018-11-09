# -*- coding: utf-8 -*-
{
    'name': "Costa Rica Tipo de Cambio",
    'author': "Jimmy Cruz - jimmycruzv@gmail.com",
    'summary': """
        Actualiza el tipo de cambio de
        venta automáticamente""",

    'description': """
        Este módulo consume el servicio web del 
        Banco Central de Costa Rica y actualiza el tipo de cambio de
        venta en Odoo de manera automática, de igual manera crea una 
        bitácora con los eventos generados cada día
    """,
    'website': "web-builds.com",
    'category': 'Currency',
    'version': '1.2',
    'depends': ['base','account'],
    'data': [
        'views/crc_currency_rate_view.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',
        'data/res_currency_update.xml',
    ],
    "application" : True,

}