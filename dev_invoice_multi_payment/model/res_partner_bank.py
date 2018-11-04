# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

    
class res_partner_bank(models.Model):
    _inherit = 'res.partner.bank'
    
    payment_type = fields.Many2one('dev.payment.type',string='Payment Type')
    acc_number = fields.Char('Account Number', required=False)
            
            
            

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:             
