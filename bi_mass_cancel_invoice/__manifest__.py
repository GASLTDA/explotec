# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Mass Cancel Invoice(s)',
    'version': '11.0.0.1',
    'author':'BrowseInfo',
    'category': 'Base',
    'sequence': 15,
    'summary': 'This apps helps to cancel invoices on mass scale',
    'description': """Allow you to cancel the invoice

    mass cancel invoices
    mass cancel customer invoice
    mass cancel vendor bills
    mass cancel supplier invoice
    mass cancel customer invoice
    mass invoice cancel
    mass vendor bills cancel
    mass vendor bill cancel
    mass customer invoice cancel
    mass customer invoices cancel
    mass vendor bill cancel
    mass vendor bills cancel
    cancel mass invoices
    cancel mass customer invoices
    cancel mass invoices
    cancel mass vendor bills
    cancel mass sales invoice

     """,
    "price": 10,
    "currency": 'EUR',
    'website': 'http://www.browseinfo.in',
    'depends': ['base','sale_management','account_invoicing'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/mass_cancel_invoice_view.xml',
        'views/main_mass_cancel.xml',

        ],
   
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    "images":['static/description/Banner.png'],
}
