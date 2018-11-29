# coding: utf-8
from odoo import fields, models


class AccountFinancialReportLine(models.Model):
    _inherit = "account.financial.html.report.line"

    def _query_get_select_sum(self, currency_table):
        """ Little function to help building the SELECT statement when
        computing the report lines.

            @param currency_table: dictionary containing the foreign
                currencies (key) and their factor (value) compared to the
                current user's company currency
            @returns: the string and parameters to use for the SELECT
        """
        extra_params = []
        select = '''
            COALESCE(SUM(\"account_move_line\".balance), 0) AS balance,
            COALESCE(SUM(\"account_move_line\".amount_residual), 0)
                AS amount_residual,
            COALESCE(SUM(\"account_move_line\".debit), 0) AS debit,
            COALESCE(SUM(\"account_move_line\".credit), 0) AS credit
        '''
        if currency_table and not self._context.get('date_from', False):
            date = self._context.get('date_to') or fields.Date.today()
            select = 'COALESCE(SUM(CASE '
            query_currency_ratio = '''COALESCE((
                SELECT r.rate FROM res_currency_rate r
                WHERE r.currency_id = %s AND
                    r.name <= %s AND
                    (r.company_id IS NULL OR r.company_id = %s)
                ORDER BY r.company_id, r.name
                DESC LIMIT 1), 1) / COALESCE((
                SELECT r.rate FROM res_currency_rate r
                WHERE r.currency_id = account_move_line.company_currency_id AND
                    r.name <= %s AND
                    (r.company_id IS NULL OR r.company_id = %s)
                ORDER BY r.company_id, r.name
                DESC LIMIT 1), 1)'''
            # pylint: disable=unused-variable
            for currency_id, rate in currency_table.items():
                extra_params += [currency_id,
                                 self.env.user.company_id.currency_id.id, date,
                                 self.env.user.company_id.id, date,
                                 self.env.user.company_id.id]
                select += """
                    WHEN \"account_move_line\".company_currency_id = %s
                    THEN \"account_move_line\".balance *
                    """ + query_currency_ratio
            select += """
                ELSE \"account_move_line\".balance END), 0) AS balance,
                COALESCE(SUM(CASE """
            for currency_id, rate in currency_table.items():
                extra_params += [currency_id,
                                 self.env.user.company_id.currency_id.id, date,
                                 self.env.user.company_id.id, date,
                                 self.env.user.company_id.id]
                select += """
                    WHEN \"account_move_line\".company_currency_id = %s
                    THEN \"account_move_line\".amount_residual *
                    """ + query_currency_ratio
            select += """
                ELSE \"account_move_line\".amount_residual END), 0)
                AS amount_residual, COALESCE(SUM(CASE """
            for currency_id, rate in currency_table.items():
                extra_params += [currency_id,
                                 self.env.user.company_id.currency_id.id, date,
                                 self.env.user.company_id.id, date,
                                 self.env.user.company_id.id]
                select += """
                WHEN \"account_move_line\".company_currency_id = %s
                THEN \"account_move_line\".debit * """ + query_currency_ratio
            select += """
                ELSE \"account_move_line\".debit END), 0) AS debit,
                COALESCE(SUM(CASE """
            for currency_id, rate in currency_table.items():
                extra_params += [currency_id,
                                 self.env.user.company_id.currency_id.id, date,
                                 self.env.user.company_id.id, date,
                                 self.env.user.company_id.id]
                select += """
                    WHEN \"account_move_line\".company_currency_id = %s
                    THEN \"account_move_line\".credit *
                    """ + query_currency_ratio
            select += 'ELSE \"account_move_line\".credit END), 0) AS credit'
        elif currency_table and self._context.get('date_from', False):
            select = 'COALESCE(SUM(CASE '
            query_currency_ratio = '''COALESCE((
                SELECT r.rate FROM res_currency_rate r
                WHERE r.currency_id = %s AND
                    r.name <= account_move_line.date AND
                    (r.company_id IS NULL OR r.company_id = %s)
                ORDER BY r.company_id, r.name
                DESC LIMIT 1), 1) / COALESCE((
                SELECT r.rate FROM res_currency_rate r
                WHERE r.currency_id = account_move_line.company_currency_id AND
                    r.name <= account_move_line.date AND
                    (r.company_id IS NULL OR r.company_id = %s)
                ORDER BY r.company_id, r.name
                DESC LIMIT 1), 1)'''
            for currency_id, rate in currency_table.items():
                extra_params += [currency_id,
                                 self.env.user.company_id.currency_id.id,
                                 self.env.user.company_id.id,
                                 self.env.user.company_id.id]
                select += """
                    WHEN \"account_move_line\".company_currency_id = %s
                    THEN \"account_move_line\".balance *
                    """ + query_currency_ratio
            select += """
                ELSE \"account_move_line\".balance END), 0) AS balance,
                COALESCE(SUM(CASE """
            for currency_id, rate in currency_table.items():
                extra_params += [currency_id,
                                 self.env.user.company_id.currency_id.id,
                                 self.env.user.company_id.id,
                                 self.env.user.company_id.id]
                select += """
                    WHEN \"account_move_line\".company_currency_id = %s
                    THEN \"account_move_line\".amount_residual *
                    """ + query_currency_ratio
            select += """
                ELSE \"account_move_line\".amount_residual END), 0)
                AS amount_residual, COALESCE(SUM(CASE """
            for currency_id, rate in currency_table.items():
                extra_params += [currency_id,
                                 self.env.user.company_id.currency_id.id,
                                 self.env.user.company_id.id,
                                 self.env.user.company_id.id]
                select += """
                    WHEN \"account_move_line\".company_currency_id = %s
                    THEN \"account_move_line\".debit *
                    """ + query_currency_ratio
            select += """
                ELSE \"account_move_line\".debit END), 0) AS debit,
                COALESCE(SUM(CASE """
            for currency_id, rate in currency_table.items():
                extra_params += [currency_id,
                                 self.env.user.company_id.currency_id.id,
                                 self.env.user.company_id.id,
                                 self.env.user.company_id.id]
                select += """
                    WHEN \"account_move_line\".company_currency_id = %s
                    THEN \"account_move_line\".credit *
                    """ + query_currency_ratio
            select += 'ELSE \"account_move_line\".credit END), 0) AS credit'

        if self.env.context.get('cash_basis'):
            for field in ['debit', 'credit', 'balance']:
                # replace the columns selected but not the final column
                # name (... AS <field>)
                number_of_occurence = len(select.split(field)) - 1
                select = select.replace(field, field + '_cash_basis',
                                        number_of_occurence - 1)
        return select, extra_params
