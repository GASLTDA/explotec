# -*- coding: utf-8 -*-
""" HR Payroll Multi Currency """

import logging

from odoo import fields, models

LOGGER = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    currency_id = fields.Many2one(comodel_name="res.currency", related='',
                                  readonly=False, required=True, store=True,
                                  default=lambda
                                      self: self.env.user.company_id.currency_id.id)
