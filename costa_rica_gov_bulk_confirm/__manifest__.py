{
    'name' : 'Costa Rica Government Submission Bulk Confirm',
    'version' : '1.1',
    'author' : 'Janeindiran',
    'summary': 'Send Invoices and Track Payments',
    'sequence': 30,

    'category': 'Accounting',
    'depends' : ['costa_rica_gov_submission'],
    'installable': True,
    'website': 'https://janeindiran.com',
    'application': False,
    'auto_install': False,
    'data': [
        #import data
        'security/ir.model.access.csv',
        'views/wizard.xml',

    ]

}
