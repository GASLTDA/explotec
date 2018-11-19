# -*- coding: utf-8 -*-
""" HR Payroll Multi Currency """

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    '''HR Payroll Multi-Currency
    
    Add currency in payslip to allow generate journal entry based on it'''

    currency_id = fields.Many2one('res.currency', string='Currency',
                                  states={'draft': [('readonly', False)]},
                                  readonly=True,
                                  required=True, default=lambda
            self: self.contract_id.currency_id.id or self.env.user.company_id.currency_id.id)

    @api.onchange('contract_id')
    def onchange_contract(self):
        '''update currency if contract changed'''
        result = super(HrPayslip, self).onchange_contract()
        if self.contract_id:
            self.currency_id = self.contract_id.currency_id.id
        return result

    @api.multi
    def action_payslip_done(self):
        '''override main function to allow to generate journal entry
        based on payslip currency_id'''
        precision = self.env['decimal.precision'].precision_get('Payroll')
        for slip in self:
            slip.compute_sheet()
            slip.write({'state': 'done'})
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date or slip.date_to
            name = _('Payslip of %s') % (slip.employee_id.name)
            move_dict = {
                'narration': name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'date': date,
            }
            for line in slip.details_by_salary_rule_category:
                amount = slip.credit_note and -line.total or line.total
                # get company base amount
                from_cur = slip.currency_id
                currency = line.env.user.company_id.currency_id.with_context(
                    date=slip.date or slip.date_to or fields.Date.context_today(
                        self))
                base_amount = from_cur.compute(amount,
                                               currency)

                if float_is_zero(base_amount, precision_digits=precision):
                    continue
                debit_account_id = line.salary_rule_id.account_debit.id
                credit_account_id = line.salary_rule_id.account_credit.id
                if debit_account_id:
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(
                            credit_account=False),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': base_amount > 0.0 and base_amount or 0.0,
                        'credit': base_amount < 0.0 and -base_amount or 0.0,
                        'amount_currency': amount if slip.currency_id.id != slip.company_id.currency_id.id else False,
                        'currency_id': from_cur.id if slip.currency_id.id != slip.company_id.currency_id.id else False,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2][
                        'credit']
                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': base_amount < 0.0 and -base_amount or 0.0,
                        'credit': base_amount > 0.0 and base_amount or 0.0,
                        'amount_currency': -amount if slip.currency_id.id != slip.company_id.currency_id.id else False,
                        'currency_id': from_cur.id if slip.currency_id.id != slip.company_id.currency_id.id else False,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2][
                        'debit']
            if float_compare(credit_sum, debit_sum,
                             precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise UserError(_(
                        'The Expense Journal "%s" has not properly configured the Credit Account!') % (
                                        slip.journal_id.name))

                # get company debit_sum - credit_sum
                debit_credit_sum = currency.compute((debit_sum - credit_sum),
                                                    from_cur)
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                    'currency_id': from_cur.id if slip.currency_id.id != slip.company_id.currency_id.id else False,
                    'amount_currency': -debit_credit_sum  if slip.currency_id.id != slip.company_id.currency_id.id else False,
                })
                line_ids.append(adjust_credit)
            elif float_compare(debit_sum, credit_sum,
                               precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise UserError(_(
                        'The Expense Journal "%s" has not properly configured the Debit Account!') % (
                                        slip.journal_id.name))

                # get company credit_sum - debit_sum
                credit_debit_sum = currency.compute(
                    (credit_sum - debit_sum),
                    from_cur)
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': credit_sum - debit_sum,
                    'currency_id': from_cur.id if slip.currency_id.id != slip.company_id.currency_id.id else False,
                    'amount_currency': credit_debit_sum  if slip.currency_id.id != slip.company_id.currency_id.id else False,
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)
            move_dict['line_ids'] = line_ids
            move = self.env['account.move'].create(move_dict)
            slip.write({'move_id': move.id, 'date': date})
            move.post()
