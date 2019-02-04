# -*- coding: utf-8 -*-
{
    'name': "Explotec Customization",
    'author': "Hadoopt Technologies Private Limited",
    'website': "https://www.hadoopt.com",
    'depends': ['base','product'],
    'data': [
        'data/ir_sequence.xml',
        'views/res_company.xml'
    ],
    'installable': True,
    'auto_install': False,
    'post_init_hook': '_auto_install_data',
}
