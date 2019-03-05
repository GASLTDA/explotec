# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt. Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': "HR Payroll Department Statement Excel Report",
    'version': '1.0',
    'price': 85.0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'category': 'Human Resources',
    'summary':  """This module allow to print department wise payroll summary in excel format.""",
    'description': """
This module allow to print department wise payroll summary in excel format.
        HR Payroll Department Statement Modules:
        - Payroll Department Statement
hr_payroll
payroll statement
payroll register
hr payroll
payroll
payslips report
payslip report
summary payroll
summary payslip
monthly statement by department
payroll by department
employee department wise payroll
payroll register
print payslip
payslip register
payslip in excel
excel report hr payroll statement by department
department wise payroll
payroll report
payroll department report
department wise payroll
department payroll statement
payroll department statement
payslip report
hr payslip
employee payslip by department
employee payroll
hr payroll
hr_payroll
hr_payroll_department_statement
payroll report
payroll reports
payroll analysis
department wise payroll statement
payroll statement
monthly payroll
payroll data
payroll excel
payslip excel
payslip send by email
payslip by email


department wise payslips report
    """,
    
    'author': "Probuse Consulting Service Pvt Ltd",
    'website': "www.probuse.com",
    'depends': ['hr_payroll'],
    'data': [
        "security/ir.model.access.csv",
        'wizard/payroll_department_statement.xml',
    ],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
