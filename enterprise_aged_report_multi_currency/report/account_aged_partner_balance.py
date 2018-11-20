from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models
from odoo.tools import float_is_zero
from odoo.exceptions import UserError


class ReportAgedPartnerBalance(models.AbstractModel):
    _inherit = 'report.account.report_agedpartnerbalance'

    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length, currency):
        periods = {}
        start = datetime.strptime(date_from, "%Y-%m-%d")
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            periods[str(i)] = {
                'name': (i != 0 and (str((5 - (i + 1)) * period_length) + '-' + str((5 - i) * period_length)) or (
                '+' + str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)

        res = []
        total = []
        cr = self.env.cr
        user_company = self.env.user.company_id.id
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type))
        # build the reconciliation clause to see what partner needs to be printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where create_date > %s',
                   (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, user_company)
        query = '''
            SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
            FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND ''' + reconciliation_clause + '''
                AND (l.date <= %s)
                AND l.company_id = %s
            ORDER BY UPPER(res_partner.name)'''
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
        lines = dict((partner['partner_id'] or False, []) for partner in partners)
        if not partner_ids:
            return [], [], []

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) > %s)\
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND (l.date <= %s)
                AND l.company_id = %s'''
        cr.execute(query,
                   (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, user_company))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []

        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = line.balance

            if line.balance == 0:
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.max_date <= date_from:
                    line_amount += partial_line.amount
            for partial_line in line.matched_credit_ids:
                if partial_line.max_date <= date_from:
                    line_amount -= partial_line.amount
            if not self.env.user.company_id.currency_id.is_zero(line_amount):

                if line.currency_id and line.currency_id.id != line.company_id.currency_id.id:
                    journal_date = line.move_id.date
                    rate = self.env['res.currency.rate'].search(
                        [('name', '<=', journal_date), ('currency_id', '=', line.currency_id.id)])


                    currency_id = line.currency_id
                    if rate:
                        rate = rate[0].rate
                        if currency_id.id == currency.id:
                            undue_amounts[partner_id] += line_amount * rate
                            lines[partner_id].append({
                                'line': line,
                                'amount': line_amount * rate,
                                'period': 6,
                                'currency_id': currency_id,
                            })
                    else:

                        lang = self.env['res.lang'].sudo().search([('code','=',self.env.user.partner_id.lang)])

                        raise UserError("Journal - "+ line.move_id.name + '\n'+ 'Exchange rate not defined for '+ line.currency_id.name + ' on ' + datetime.strftime(datetime.strptime(journal_date,'%Y-%m-%d'),lang.date_format))

                else:

                    if line.company_id.currency_id.id == currency.id:
                        undue_amounts[partner_id] += line_amount

                        lines[partner_id].append({
                            'line': line,
                            'amount': line_amount,
                            'period': 6,
                            'currency_id': line.company_id.currency_id,
                        })

        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, user_company)

            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    AND l.company_id = %s'''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []

            for line in self.env['account.move.line'].browse(aml_ids):
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = line.balance
                if line.balance == 0:
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += partial_line.amount
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= partial_line.amount

                if not self.env.user.company_id.currency_id.is_zero(line_amount):


                    if line.currency_id and line.currency_id.id != line.company_id.currency_id.id:
                        journal_date = line.move_id.date
                        rate = self.env['res.currency.rate'].search(
                            [('name', '<=', journal_date), ('currency_id', '=', line.currency_id.id)])
                        currency_id = line.currency_id

                        if rate:
                            rate = rate[0].rate

                            if currency_id.id == currency.id:
                                partners_amount[partner_id] += line_amount * rate
                                lines[partner_id].append({
                                    'line': line,
                                    'amount': line_amount * rate,
                                    'period': i + 1,
                                    'currency_id': currency_id,
                                })
                        else:

                            lang = self.env['res.lang'].sudo().search([('code','=',self.env.user.partner_id.lang)])

                            raise UserError("Journal - "+ line.move_id.name + '\n'+ 'Exchange rate not defined for '+ line.currency_id.name + ' on ' + datetime.strftime(datetime.strptime(journal_date,'%Y-%m-%d'),lang.date_format))
                    else:
                        if line.company_id.currency_id.id == currency.id:
                            partners_amount[partner_id] += line_amount
                            lines[partner_id].append({
                                'line': line,
                                'amount': line_amount,
                                'period': i + 1,
                                'currency_id': line.company_id.currency_id,
                            })
            history.append(partners_amount)

        for partner in partners:
            if partner['partner_id'] in lines:
                if len(lines[partner['partner_id']]) > 0:
                    if partner['partner_id'] is None:
                        partner['partner_id'] = False
                    at_least_one_amount = False
                    values = {}
                    undue_amt = 0.0
                    if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                        undue_amt = undue_amounts[partner['partner_id']]

                    total[6] = total[6] + undue_amt
                    values['direction'] = undue_amt
                    if not float_is_zero(values['direction'],
                                         precision_rounding=currency.rounding):
                        at_least_one_amount = True

                    for i in range(5):
                        during = False
                        if partner['partner_id'] in history[i]:
                            during = [history[i][partner['partner_id']]]
                        # Adding counter
                        total[(i)] = total[(i)] + (during and during[0] or 0)
                        values[str(i)] = during and during[0] or 0.0
                        if not float_is_zero(values[str(i)],
                                             precision_rounding=currency.rounding):
                            at_least_one_amount = True
                    values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
                    ## Add for total
                    total[(i + 1)] += values['total']
                    values['partner_id'] = partner['partner_id']
                    if partner['partner_id']:
                        browsed_partner = self.env['res.partner'].browse(partner['partner_id'])
                        values['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 and browsed_partner.name[
                                                                                                      0:40] + '...' or browsed_partner.name
                        values['trust'] = browsed_partner.trust
                    else:
                        values['name'] = _('Unknown Partner')
                        values['trust'] = False

                    if at_least_one_amount:
                        res.append(values)

        return res, total, lines
