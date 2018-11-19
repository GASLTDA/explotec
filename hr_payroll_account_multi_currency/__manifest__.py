# -*- coding: utf-8 -*-
{
  "name"                 :  "HR Payroll Multi-Currency",
  'summary'              :  """Allow to create journal entry for payslip with multi currency""",
  "category"             :  "HR",
  "version"              :  "11.0.1.0.0",
  "author"               :  "Abdallah Mohamed",
  "license"              :  "OPL-1",
  "maintainer"           :  "Abdallah Mohammed",
  "website"              :  "https://www.abdalla.work/r/mW1",
  "support"              :  "https://www.abdalla.work/r/mW1",
  "description"          :  """ODOO HR Payroll Accounting Multi Currency""",
  "depends"              :  [
                             'hr_payroll_account',
                            ],
  "data"                 :  [
                             'views/hr_contract.xml',
                             'views/hr_payslip.xml',
                             'reports/report_payslip.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  False,
  "installable"          :  True,
  "price"                :  20,
  "currency"             :  "EUR",
  'sequence'             : 1
}