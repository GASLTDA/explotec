# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Mass Accounting Cancel',
    'version': '10.0',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'author': "Odoo Tips",
    'website': 'http://www.gotodoo.com/',
    'depends': ['account', 'account_invoicing', 'account_payment',
                ],
    'images': ['images/main_screenshot.png'],
    'data': [
             'wizard/mass_accounting_cancel_view.xml',
             ],
    'installable': True,
    'application': True,
}
