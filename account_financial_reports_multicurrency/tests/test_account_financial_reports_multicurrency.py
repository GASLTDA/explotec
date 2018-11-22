# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.tests.common import TransactionCase


class TestAccFinRepMulticurrency(TransactionCase):

    def setUp(self):
        super(TestAccFinRepMulticurrency, self).setUp()
        self.my_receivables_report = self.env.ref(
            'account_financial_reports_multicurrency.my_receivables')
        self.my_incomes_report = self.env.ref(
            'account_financial_reports_multicurrency.my_incomes')
        self.main_company = self.env.ref('base.main_company')
        self.holding_company = self.env.ref(
            'account_financial_reports_multicurrency.company_holding'
        )
        self.user_root = self.env.ref('base.user_root')
        self.user_root.company_ids |= self.holding_company

    def test_001_my_receivables_report_usd(self):
        options = {'cash_basis': False,
                   'date': {'date': '2017-12-31', 'string': '2017',
                            'filter': 'last_year'}, 'unfold_all': None,
                   'multi_company': [{'id': self.holding_company.id,
                                      'name': self.holding_company.name,
                                      'selected': True},
                                     {'id': self.main_company.id,
                                      'name': self.main_company.name,
                                      'selected': True}],
                   'comparison': {'date': '2016-12-31',
                                  'periods':
                                  [{'date': '2016-12-31', 'string': '2016'},
                                   {'date': '2015-12-31', 'string': '2015'}],
                                  'string': '2016', 'number_period': 2,
                                  'filter': 'previous_period'},
                   'journals': None, 'all_entries': True}
        expected_values = [{'name': '$ 3,000.00', 'no_format_name': 3000.0},
                           {'name': '$ 2,000.00', 'no_format_name': 2000.0},
                           {'name': '$ 1,000.00', 'no_format_name': 1000.0}]
        result = self.my_receivables_report.get_lines(options)[0].get(
            'columns')
        self.assertEquals(expected_values, result, 'Different values for"My \
                          Receivables" report.')

    def test_002_my_incomes_report_usd(self):
        options = {'comparison': {'number_period': 2, 'date_to': '2016-12-31',
                                  'filter': 'previous_period',
                                  'date_from': '2016-01-02', 'string': '2016',
                                  'periods':
                                  [{'date_from': '2016-01-02',
                                    'string': '2016', 'date_to': '2016-12-31'},
                                   {'date_from': '2015-01-01',
                                    'string': '2015',
                                    'date_to': '2015-12-31'}]},
                   'cash_basis': False, 'date': {'date_from': '2017-01-01',
                                                 'string': '2017',
                                                 'date_to': '2017-12-31',
                                                 'filter': 'last_year'},
                   'all_entries': True, 'multi_company':
                   [{'id': self.holding_company.id,
                     'name': self.holding_company.name, 'selected': False},
                    {'id': self.main_company.id,
                     'name': self.main_company.name, 'selected': True}]}
        expected_values = [{'name': '$ 1,000.00', 'no_format_name': 1000.0},
                           {'name': '$ 1,000.00', 'no_format_name': 1000.0},
                           {'name': '$ 1,000.00', 'no_format_name': 1000.0}]
        result = self.my_incomes_report.get_lines(options)[0].get(
            'columns')
        self.assertEquals(expected_values, result, 'Different values for "My \
                          Incomes" report.')

    def test_003_my_receivables_report_eur(self):
        self.user_root.write({'company_id': self.holding_company.id})
        options = {'cash_basis': False,
                   'date': {'date': '2017-12-31', 'string': '2017',
                            'filter': 'last_year'}, 'unfold_all': None,
                   'multi_company': [{'id': self.holding_company.id,
                                      'name': self.holding_company.name,
                                      'selected': True},
                                     {'id': self.main_company.id,
                                      'name': self.main_company.name,
                                      'selected': True}],
                   'comparison': {'date': '2016-12-31',
                                  'periods':
                                  [{'date': '2016-12-31', 'string': '2016'},
                                   {'date': '2015-12-31', 'string': '2015'}],
                                  'string': '2016', 'number_period': 2,
                                  'filter': 'previous_period'},
                   'journals': None, 'all_entries': True}
        expected_values = [
            {'name': '2,493.77 €', 'no_format_name': 2493.7655860349128},
            {'name': '1,901.86 €', 'no_format_name': 1901.863826550019},
            {'name': '920.81 €', 'no_format_name': 920.8103130755064}]
        result = self.my_receivables_report.get_lines(options)[0].get(
            'columns')
        self.assertEquals(expected_values, result, 'Different values for"My \
                          Receivables (EUR)" report.')

    def test_004_my_incomes_report_eur(self):
        self.user_root.write({'company_id': self.holding_company.id})
        options = {'comparison': {'number_period': 2, 'date_to': '2016-12-31',
                                  'filter': 'previous_period',
                                  'date_from': '2016-01-02', 'string': '2016',
                                  'periods':
                                  [{'date_from': '2016-01-02',
                                    'string': '2016', 'date_to': '2016-12-31'},
                                   {'date_from': '2015-01-01',
                                    'string': '2015',
                                    'date_to': '2015-12-31'}]},
                   'cash_basis': False, 'date': {'date_from': '2017-01-01',
                                                 'string': '2017',
                                                 'date_to': '2017-12-31',
                                                 'filter': 'last_year'},
                   'all_entries': True, 'multi_company':
                   [{'id': self.holding_company.id,
                     'name': self.holding_company.name, 'selected': True},
                    {'id': self.main_company.id,
                     'name': self.main_company.name, 'selected': True}]}
        expected_values = [
            {'name': '950.93 €', 'no_format_name': 950.9319132750095},
            {'name': '920.81 €', 'no_format_name': 920.8103130755064},
            {'name': '833.13 €', 'no_format_name': 833.1250520703157}]
        result = self.my_incomes_report.get_lines(options)[0].get('columns')
        self.assertEquals(expected_values, result, 'Different values for"My \
                          Incomes (EUR)" report.')
