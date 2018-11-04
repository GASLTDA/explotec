# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://devintellecs.com>).
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

    
class advance_payment_line(models.Model):
    _name = 'advance.payment.line'
    
    
    invoice_id = fields.Many2one('account.invoice',string='Invoice')
    account_id = fields.Many2one('account.account', string="Account")
    date = fields.Date(string="Date")
    due_date = fields.Date(string="Due Date")
    original_amount = fields.Float(string="Original Amount")
    balance_amount = fields.Float(string="Balance Amount")
    full_reconclle = fields.Boolean(string="Full Reconclle")
    allocation = fields.Float(string="Allocation")
    account_payment_id = fields.Many2one('account.payment')
    diff_amt = fields.Float('Remaining Amount',compute='get_diff_amount',)
    
    @api.multi
    @api.depends('balance_amount','allocation')
    def get_diff_amount(self):
        for line in self: 
            line.diff_amt = line.balance_amount - line.allocation
    
    @api.onchange('full_reconclle')
    def onchange_full_reconclle(self):
        if self.full_reconclle:
            self.allocation = self.balance_amount
            
    @api.onchange('allocation')
    def onchange_allocation(self):
        if self.allocation:
            if self.allocation >= self.balance_amount:
                self.full_reconclle = True
            else:
                self.full_reconclle = False
            
    
             
