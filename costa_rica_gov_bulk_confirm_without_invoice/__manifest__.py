{
    'name' : 'Costa Rica Government Submission Bulk Confirm Without Invoice',
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
        'data/scheduler.xml',

        'views/comfirmar_without_invoice.xml',
        'views/wizard.xml',
    ]

}
