from odoo import models, api, _
from odoo.tools import format_date


class report_account_aged_partner(models.AbstractModel):
    _inherit = "account.aged.partner"


    def get_columns_name(self, options):
        columns = [{}]
        columns += [{'name': v, 'class': 'number'} for v in [_("Not due on %s") % format_date(self.env, options['date']['date']), _("0-30"), _("30-60"), _("60-90"), _("90-120"), _("Older"), _("Total")]]
        return columns

    def get_templates(self):
        templates = super(report_account_aged_partner, self).get_templates()
        templates['main_template'] = 'enterprise_aged_report_multi_currency.main_template'
        try:
            self.env['ir.ui.view'].get_view_id('account_reports.template_aged_partner_balance_line_report')
            templates['line_template'] = 'account_reports.template_aged_partner_balance_line_report'
        except ValueError:
            pass
        return templates

    @api.model
    def get_lines(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        counter = 0
        current_currency = None
        currencies = self.env['res.currency'].search([])
        for currency in currencies:
            if current_currency == None:
                current_currency = currency

            if current_currency.id != currency.id:
                current_currency = currency
                counter = 0

            results, total, amls = self.env['report.account.report_agedpartnerbalance']._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30,currency)

            for values in results:
                if line_id and 'partner_%s' % (str(values['partner_id'])+"_"+currency.name) != line_id:
                    continue

                if counter == 0:
                    lines.append({ 'id': currency.name+'_0',
                                   'name': '',
                                   'class': 'total',
                                   'level': 1,
                                   'columns': [{'name': ''} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                                   'trust': '',
                                   'unfoldable': False,
                                   'hide_duplicate':True
                                   })
                    lines.append({ 'id': currency.name+'_1',
                                   'name': '',
                                   'level': 1,
                                   'class': '',
                                   'columns': [{'name': ''} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                                   'trust': '',
                                   'unfoldable': False,
                                   'hide_duplicate':True
                                   })
                    lines.append({ 'id': currency.name+'_2',
                                   'name': currency.name,
                                   'class': 'total',
                                   'level': 1,
                                   'columns': [{'name': ''} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                                   'trust': '',
                                   'unfoldable': False,
                                   'hide_duplicate':True
                                   })

                counter += 1

                vals = {
                    'id': 'partner_%s' % (str(values['partner_id'])+"_"+currency.name),
                    'name': values['name'],
                    'level': 2,
                    'columns': [{'name': self.format_value(sign * v, currency)} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                    'trust': values['trust'],
                    'unfoldable': True,
                    'unfolded': 'partner_%s' % (str(values['partner_id'])+"_"+currency.name) in options.get('unfolded_lines'),
                }
                lines.append(vals)
                if 'partner_%s' % (str(values['partner_id'])+"_"+currency.name) in options.get('unfolded_lines'):
                    for line in amls[values['partner_id']]:
                        aml = line['line']
                        caret_type = 'account.move'
                        if aml.invoice_id:
                            caret_type = 'account.invoice.in' if aml.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                        elif aml.payment_id:
                            caret_type = 'account.payment'
                        vals = {
                            'id': aml.id,
                            'name': aml.move_id.name if aml.move_id.name else '/',
                            'caret_options': caret_type,
                            'level': 4,
                            'parent_id': 'partner_%s' % (str(values['partner_id'])+"_"+currency.name),
                            'columns': [{'name': v} for v in [line['period'] == 6-i and self.format_value(sign * line['amount'],line['currency_id']) or '' for i in range(7)]],
                        }
                        lines.append(vals)

                    vals = {
                        'id': (str(values['partner_id'])+"_"+currency.name),
                        'class': 'o_account_reports_domain_total',
                        'name': _('Total '),
                        'parent_id': 'partner_%s' % (str(values['partner_id'])+"_"+currency.name),
                        'columns': [{'name': self.format_value(sign * v, currency)} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                    }
                    lines.append(vals)

            if total and not line_id and len(lines) > 0:
                total_line = {
                    'id': 0,
                    'name': _('Total'),
                    'class': 'total',
                    'level': 'None',
                    'columns': [{'name': self.format_value(sign * v, currency)} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
                }

                if abs(total[6]) != 0 or abs(total[4]) != 0 or abs(total[3]) != 0 or abs(total[2]) != 0 or abs(total[1]) != 0 or abs(total[0]) != 0 or abs(total[5]) > 0:
                    lines.append(total_line)
        return lines

    @api.model
    def get_lines_no_currency(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        current_currency = None
        currencies = self.env['res.currency'].search([])

        for currency in currencies:
            if current_currency == None:
                current_currency = currency

            if current_currency.id != currency.id:
                current_currency = currency

            results, total, amls = self.env['report.account.report_agedpartnerbalance']._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30,currency)

            for values in results:
                if line_id and 'partner_%s' % (str(values['partner_id'])+"_"+currency.name) != line_id:
                    continue

                vals = {
                    'id': 'partner_%s' % (str(values['partner_id'])+"_"+currency.name),
                    'name': values['name'],
                    'level': 2,
                    'columns': [{'name': self.format_value(sign * v, currency)} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                    'trust': values['trust'],
                    'unfoldable': True,
                    'unfolded': 'partner_%s' % (str(values['partner_id'])+"_"+currency.name) in options.get('unfolded_lines'),
                }
                lines.append(vals)
                if 'partner_%s' % (str(values['partner_id'])+"_"+currency.name) in options.get('unfolded_lines'):
                    for line in amls[values['partner_id']]:
                        aml = line['line']
                        caret_type = 'account.move'
                        if aml.invoice_id:
                            caret_type = 'account.invoice.in' if aml.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                        elif aml.payment_id:
                            caret_type = 'account.payment'
                        vals = {
                            'id': aml.id,
                            'name': aml.move_id.name if aml.move_id.name else '/',
                            'caret_options': caret_type,
                            'level': 4,
                            'parent_id': 'partner_%s' % (str(values['partner_id'])+"_"+currency.name),
                            'columns': [{'name': v} for v in [line['period'] == 6-i and self.format_value(sign * line['amount'],line['currency_id']) or '' for i in range(7)]],
                        }
                        lines.append(vals)
                    vals = {
                            'id': (str(values['partner_id'])+"_"+currency.name),
                            'class': 'o_account_reports_domain_total',
                            'name': _('Total '),
                            'parent_id': 'partner_%s' % (str(values['partner_id'])+"_"+currency.name),
                            'columns': [{'name': self.format_value(sign * v, currency)} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                        }
                    lines.append(vals)

            if total and not line_id and len(lines) > 0:
                total_line = {
                    'id': 0,
                    'name': _('Total'),
                    'class': 'total',
                    'level': 'None',
                    'columns': [{'name': self.format_value(sign * v, currency)} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
                }
                lines.append(total_line)

        return lines
