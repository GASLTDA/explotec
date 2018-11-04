# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################
{
    'name': 'Multiple Invoice Payment',
    'version': '1.0',
    'sequence':1,
    'category': 'Generic Modules/Accounting',
    'summary': 'odoo App will allow multiple invoice payment from payment and invoice screen.',
    'description': """
        App will allow multiple invoice payment from payment and invoice screen.
        
       Multiple invoice payment, Invoice Multiple payment, Payment , Partial Invoice Payment, Full invoice Payment,Payment write off,   Payment Invoice, 
    Multiple invoice payment
    Credit notes payment
    How can create multiple invoice
    How can create multiple invoice odoo
    Multiple invoice payment in single click
    Make multiple invoice payment
    Partial invoice payment
    Credit note multiple payment
    Pay multiple invoice
    Paid multiple invoice
    Invoice payment automatic
    Invoice wise payment
    Odoo invoice payment
    Openerp invoice payment
    Partial invoice
    Partial payment
    Pay partially invoice
    Pay partially payment
    Invoice generation
    Invoice payment
    Website payment receipt
    Multiple bill payment
    Multiple vendor bill payment
    Vendor bill 
    Batch invoice in odoo
    bulk invoice payment in odoo
    bulk payment 
    mass payment in odoo 
    mass invoice payment
    mass invoice payment in odoo
    multi invoice ap payments
    ap payments of multiple invoice 
           
        
          
    """,
    'author': 'DevIntelle Consulting Service Pvt.Ltd', 
    'website': 'http://www.devintellecs.com',
    'depends': ['account_voucher'],
    'data': [
            'security/ir.model.access.csv',
            'view/account_payment.xml',
            'wizard/bulk_invoice_payment.xml',
            'view/res_partner_bank.xml',
            ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price':35.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
