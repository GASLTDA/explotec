from odoo.tools.misc import formatLang, format_date
from odoo import models, fields
from datetime import datetime
from odoo.tools.translate import _

class report_account_followup_report(models.AbstractModel):
    _inherit = "account.followup.report"

    def get_columns_name(self, options):
        headers = [{},
                   {'name': _(' Date '), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _(' Due Date '), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _(' Remaining Days '), 'style': 'text-align:right; white-space:nowrap;'},
                   {'name': _('Communication'), 'style': 'text-align:right; white-space:nowrap;'},
                   {'name': _(' Expected Date '), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _(' Excluded '), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _(' Total Due '), 'class': 'number', 'style': 'text-align:right; white-space:nowrap;'}
                   ]
        if self.env.context.get('print_mode'):
            headers = headers[:5] + headers[7:]
        return headers

    def get_lines(self, options, line_id=None):
        # Get date format for the lang
        partner = options.get('partner_id') and self.env['res.partner'].browse(options['partner_id']) or False
        if not partner:
            return []
        lang_code = partner.lang or self.env.user.lang or 'en_US'

        lines = []
        res = {}
        today = datetime.today().strftime('%Y-%m-%d')
        line_num = 0
        for l in partner.unreconciled_aml_ids:
            if self.env.context.get('print_mode') and l.blocked:
                continue
            currency = l.currency_id or l.company_id.currency_id
            if currency not in res:
                res[currency] = []
            res[currency].append(l)
        for currency, aml_recs in res.items():
            total = 0
            total_issued = 0
            aml_recs = sorted(aml_recs, key=lambda aml: aml.blocked)
            for aml in aml_recs:
                amount = aml.currency_id and aml.amount_residual_currency or aml.amount_residual

                a = datetime.strptime(aml.date_maturity or aml.date, '%Y-%m-%d')
                b = datetime.strptime(fields.Date.today(), '%Y-%m-%d')
                delta = a - b

                date_due = format_date(self.env, aml.date_maturity or aml.date, lang_code=lang_code)
                total += not aml.blocked and amount or 0
                is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                is_payment = aml.payment_id
                if is_overdue or is_payment:
                    total_issued += not aml.blocked and amount or 0
                if is_overdue:
                    date_due = {'name': date_due, 'class': 'color-red date', 'style': 'white-space:nowrap;text-align:center;color: red;'}
                if is_payment:
                    date_due = ''
                move_line_name = aml.invoice_id.name or aml.name
                if self.env.context.get('print_mode'):
                    move_line_name = {'name': move_line_name, 'style': 'text-align:right; white-space:normal;'}
                amount = formatLang(self.env, amount, currency_obj=currency)
                line_num += 1

                columns = [format_date(self.env, aml.date, lang_code=lang_code), date_due,delta.days, move_line_name, aml.expected_pay_date and aml.expected_pay_date +' '+ aml.internal_note or '', {'name': aml.blocked, 'blocked': aml.blocked}, amount]
                if self.env.context.get('print_mode'):
                    columns = columns[:4]+columns[6:]
                lines.append({
                    'id': aml.id,
                    'name': aml.move_id.name,
                    'caret_options': 'followup',
                    'move_id': aml.move_id.id,
                    'type': is_payment and 'payment' or 'unreconciled_aml',
                    'unfoldable': False,
                    'has_invoice': bool(aml.invoice_id),
                    'columns': [type(v) == dict and v or {'name': v} for v in columns],
                })
            totalXXX = formatLang(self.env, total, currency_obj=currency)
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': 'total',
                'unfoldable': False,
                'level': 0,
                'columns': [{'name': v} for v in ['']*(3 if self.env.context.get('print_mode') else 5) + [total >= 0 and _('Total Due') or '', totalXXX]],
            })
            if total_issued > 0:
                total_issued = formatLang(self.env, total_issued, currency_obj=currency)
                line_num += 1
                lines.append({
                    'id': line_num,
                    'name': '',
                    'class': 'total',
                    'unfoldable': False,
                    'level': 0,
                    'columns': [{'name': v} for v in ['']*(3 if self.env.context.get('print_mode') else 5) + [_('Total Overdue'), total_issued]],
                })
        return lines
