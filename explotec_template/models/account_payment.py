from odoo import models, fields, api, tools,_
from odoo.tools.misc import formatLang, format_date
import logging

try:
    from num2words import num2words
except ImportError:
    logging.getLogger(__name__).warning("The num2words python library is not installed, l10n_mx_edi features won't be fully available.")
    num2words = None

LINE_FILLER = '*'
INV_LINES_PER_STUB = 9

class report_print_check(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def amount_to_text(self, amount):
        self.ensure_one()
        def _num2words(number, lang):
            try:
                return num2words(number, lang=lang).title()
            except NotImplementedError:
                return num2words(number, lang='en').title()

        if num2words is None:
            logging.getLogger(__name__).warning("The library 'num2words' is missing, cannot render textual amounts.")
            return ""

        formatted = "%.{0}f".format(self.currency_id.decimal_places) % amount
        parts = formatted.partition('.')
        integer_value = int(parts[0])
        fractional_value = int(parts[2] or 0)

        lang_code = self.env.context.get('lang') or self.env.user.lang
        lang = self.env['res.lang'].search([('code', '=', lang_code)])
        amount_words = tools.ustr('{amt_value} {amt_word}').format(
            amt_value=_num2words(integer_value, lang=lang.iso_code),
            amt_word=self.currency_id.currency_unit_label,
        )
        if (amount - integer_value) != 0.0:
            amount_words += ' ' + _('and') + tools.ustr(' {amt_value} {amt_word}').format(
                amt_value=_num2words(fractional_value, lang=lang.iso_code),
                amt_word=self.currency_id.currency_unit_label,
            )
        return amount_words

    def get_pages(self):
        """ Returns the data structure used by the template : a list of dicts containing what to print on pages.
        """
        stub_pages = self.make_stub_pages() or [False]
        multi_stub = self.company_id.us_check_multi_stub
        pages = []
        for i, p in enumerate(stub_pages):
            pages.append({
                'sequence_number': self.check_number \
                    if (self.journal_id.check_manual_sequencing and self.check_number != 0) \
                    else False,
                'payment_date': format_date(self.env, self.payment_date),
                'partner_id': self.partner_id,
                'partner_name': self.partner_id.name,
                'currency': self.currency_id,
                'state': self.state,
                'amount': formatLang(self.env, self.amount, currency_obj=self.currency_id) if i == 0 else 'VOID',
                'amount_in_word': self.amount_to_text(self.amount) if i == 0 else 'VOID',
                'memo': self.communication,
                'stub_cropped': not multi_stub and len(self.invoice_ids) > INV_LINES_PER_STUB,
                # If the payment does not reference an invoice, there is no stub line to display
                'stub_lines': p,
            })
        return pages