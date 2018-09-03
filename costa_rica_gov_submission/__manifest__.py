{
    'name' : '(Client) Costa Rica Government Submission of invoice',
    'version' : '1.1',
    'author' : 'Janeindiran',
    'summary': 'Send Invoices and Track Payments',
    'sequence': 30,
    'description': """Text file to submit invoice information""",
    'category': 'Accounting',
    'depends' : ['base','base_setup', 'account'],
    'installable': True,
    'website': 'https://janeindiran.com',
    'application': False,
    'auto_install': False,
    'data': [
        #import data
        'security/ir.model.access.csv',
        'data/locality_province.xml',
        'data/locality_canton.xml',
        'data/locality_district.xml',
        'data/locality_locality.xml',
        # 'data/product_data.xml',
        # 'data/ir_sequence.xml',

        #views
        'views/report_invoice.xml',
        'views/res_partner.xml',
        'views/res_company.xml',
        'views/account_tax.xml',
        'views/account_invoice.xml',
        'views/product_uom.xml',
        'data/scheduler.xml',
    ]

}
