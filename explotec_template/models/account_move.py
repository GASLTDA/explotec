from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def calculate_excahnge_rate(self):
        for line in self:
            for l in line.line_ids:
                line.exchange_rate = 0.0
                if l.amount_currency > 0:
                    rate = self.env['res.currency.rate'].sudo().search(
                            [('name', '<=', line.date), ('currency_id', '=', l.currency_id.id)],limit=1)
                    if len(rate) > 0:
                        line.exchange_rate = rate.rate
                        line.curreny_exchange_rate = l.currency_id.id
                break

    image_medium = fields.Binary(related='company_id.logo')
    partner = fields.Many2one('res.partner')
    exchange_rate = fields.Monetary(compute='calculate_excahnge_rate',currency_field = 'curreny_exchange_rate')
    curreny_exchange_rate = fields.Many2one('res.currency',compute='calculate_excahnge_rate')