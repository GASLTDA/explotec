# coding: utf-8
# Copyright 2018 Vauxoo
# License OPL-1 (http://opencontent.org/openpub).

{
    'name': 'Financial Report Multicurrency',
    'summary': '''
    Allow consolidations with foreign currency
    ''',
    'author': 'Vauxoo',
    'website': 'http://www.vauxoo.com',
    'license': 'LGPL-3',
    'category': 'website',
    'version': '11.0.1.0.0',
    'depends': [
        'account_accountant',
        'account_reports',
    ],
    'test': [
    ],
    'data': [
        'data/account_financial_report_data.xml',
    ],
    'demo': [
        'demo/res_company.xml',
        'demo/res_currency.xml',
        'demo/account_move.yml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 99,
    'currency': 'EUR',
    'images': [
        'static/description/cover.png'
    ],
}
