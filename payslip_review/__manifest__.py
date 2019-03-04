{
    'name': 'HR Payroll Dashboard and Management',
    'version': '11.0.1.0',
    'price': 17.99,
    'currency': 'EUR',
    'author': 'Zadsolutions, Ahmed Hefni',
    'category': 'Generic Modules/Human Resources',
    'summary': """View, edit and compare all your company payslips in a page""",
    'license': 'GPL-3',
    'website': 'http://www.zadsolutions.com',
    'data': [
        'views/hr_payslip_views.xml',
    ],
    'images': [
        'static/description/icon.jpg',
    ],
    'depends' : ['base','web','hr_payroll'],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

