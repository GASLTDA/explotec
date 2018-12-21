# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from dateutil.relativedelta import *
from odoo.exceptions import ValidationError
from odoo.tools import format_date,formatLang
from odoo.exceptions import UserError

class StockMovementWizard(models.TransientModel):
    _name = 'stock.movement.wizard'

    name = fields.Selection([('today','Today'),('this_month','This Month'),('selected_date','Selected Date'),('date_range','Date Range')],string='Type', default='today')
    date = fields.Date()
    from_date = fields.Date()
    to_date = fields.Date()

    @api.onchange('name')
    def onchange_selected_type(self):
        if self.name == 'today':
            self.date = fields.Date.today()
            self.from_date = False
            self.to_date = False
        elif self.name == 'this_month':
            self.date = False
            self.from_date =  datetime.strftime(datetime.strptime(fields.Date.today(),'%Y-%m-%d'),'%Y-%m-01')
            self.to_date =  self.lastday_of_month()
        elif self.name == 'selected_date':
            self.from_date = False
            self.to_date = False
        elif self.name == 'date_range':
            self.date = False

    def lastday_of_month(self):
        d = datetime.strftime(datetime.strptime(fields.Date.today(),'%Y-%m-%d') + relativedelta(months=+1),'%Y-%m-01')
        d = datetime.strptime(d,'%Y-%m-%d') + relativedelta(days=-1)
        return datetime.strftime(d,'%Y-%m-%d')

    @api.multi
    def print_pdf(self):
        if self.name == 'selected_date':
            if self.date == False:
                raise UserError("Please select the date")
        if self.name == 'date_range':
            if self.from_date == False or self.to_date == False:
                raise UserError("Please select the date")
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'name': self.name,
                'date': self.date,
                'from_date': self.from_date,
                'to_date': self.to_date,
            },
        }
        return self.env.ref('report_inventory.stock_movement_report').report_action(docids=self, data=data)



class StockMovementReport(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.report_inventory.stock_movement'

    @api.model
    def get_report_values(self, docids, data=None):

        type = data['form']['name']
        date = data['form']['date']
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']

        domain = [('company_id','=',self.env.user.company_id.id)]
        if type == 'today':
            domain += [('date','>=',date + ' '+'00:00:00'),('date','<=',date + ' '+'23:59:59'),('state','=','done')]
        elif type == 'this_month':
            domain += [('date','>=',from_date + ' '+'00:00:00'),('date','<=',to_date + ' '+'23:59:59'),('state','=','done')]
        elif type == 'selected_date':
            domain += [('date','>=',date + ' '+'00:00:00'),('date','<=',date + ' '+'23:59:59'),('state','=','done')]
        elif type == 'date_range':
            domain += [('date','>=',from_date + ' '+'00:00:00'),('date','<=',to_date + ' '+'23:59:59'),('state','=','done')]

        docs = []
        move_lines = self.env['stock.move'].search(domain, order='product_id,location_dest_id asc')
        locale = self._context.get('lang') or 'en_US'
        product_id = None

        for line in move_lines:
            dest_usage =line.location_dest_id.usage
            src_usage =line.location_id.usage
            if dest_usage == 'internal' and src_usage == 'internal':
                location_type='Internal Transfer'
            elif dest_usage == 'vendor':
                location_type='Purchase'
            elif dest_usage == 'customer':
                location_type='Sale'
            elif dest_usage == 'production' and src_usage == 'Internal':
                location_type = 'Manufacturing'
            elif src_usage == 'production' and dest_usage == 'Internal':
                location_type = 'Manufacturing'
            else:
                location_type = 'Internal Transfer'


            if product_id != line.product_id.id:
                if product_id != None:

                    docs.append({ 'date': '',
                                  'type': '',
                                  'product_name': '',
                                  'product_id': '',
                                  'product_uom': '',
                                  'cost_in': '',
                                  'cost_out': '',
                                  'total_cost': '',
                                  'product_uom_qty_in': '',
                                  'product_uom_qty_out': self.get_closing_balance(line.date,line.product_id.id, line.location_dest_id.id),
                                  'reference': '<b>CLOSING BALANCE</b>',
                                  'location_id': '',
                                  'location_dest_id': '',})
                    docs.append({ 'date': '',
                                  'type': '',
                                  'product_name': '',
                                  'product_id': '',
                                  'product_uom': '',
                                  'cost_in': '',
                                  'cost_out': '',
                                  'total_cost': '',
                                  'product_uom_qty_in': '',
                                  'product_uom_qty_out': '',
                                  'reference': '',
                                  'location_id': '',
                                  'location_dest_id': '',})


                docs.append({ 'date': '',
                                  'type': '',
                                  'product_name': '',
                                  'product_id': '',
                                  'product_uom': '',
                              'cost_in': '',
                              'cost_out': '',
                              'total_cost': '',
                                  'product_uom_qty_in': '',
                                  'product_uom_qty_out': '',
                                  'reference': '',
                                  'location_id': '',
                                  'location_dest_id': '',})
                docs.append({ 'date': '<b>Item: ' + line.product_id.name + '</b>',
                                  'type': '',
                                  'product_name': '',
                                  'product_id': '',
                                  'product_uom': '',
                              'cost_in': '',
                              'cost_out': '',
                              'total_cost': '',
                                  'product_uom_qty_in': '',
                                  'product_uom_qty_out': '',
                                  'reference': '',
                                  'location_id': '',
                                  'location_dest_id': '',})
                docs.append({
                        'date': '',
                        'type':'' ,
                        'product_name':'' ,
                        'product_id': '',
                        'product_uom': '',
                        'cost_in': '',
                        'cost_out': '',
                        'total_cost': '',
                        'product_uom_qty_in':self.get_initial_balance(line.date,line.product_id.id, line.location_dest_id.id),
                        'product_uom_qty_out': '',
                        'reference': '<b>BEGINNING BALANCE<b/>',
                        'location_id': '',
                        'location_dest_id': '',
                    })

            product_uom_qty_out = 0.0
            product_uom_qty_in = 0.0
            cost_in = 0.0
            cost_out = 0.0
            total_cost = 0.0
            if location_type =='Internal Transfer':
                product_uom_qty_in  = 0.0
                product_uom_qty_out  =  line.product_uom_qty
                cost_in  = 0.0
                cost_out  = 0.0
                total_cost = 0.0
            elif location_type == 'Sale':
                product_uom_qty_in  = line.product_uom_qty
                product_uom_qty_out  = 0.0
                cost_in  = line.product_id.standard_price
                total_cost  = line.product_uom_qty * line.product_id.standard_price
                cost_out  = 0.0

            elif location_type == 'Purchase':
                product_uom_qty_in  = 0.0
                product_uom_qty_out  = line.product_uom_qty
                cost_in  = 0.0
                cost_out = line.product_id.standard_price
                total_cost = line.product_uom_qty * line.product_id.standard_price

            elif location_type == 'Manufacturing':
                product_uom_qty_in  = line.product_uom_qty
                product_uom_qty_out  = 0.0
                cost_in = 0.0
                cost_out = 0.0
                total_cost = 0.0

            docs.append({
                    'date': format_date(self.env,line.date, lang_code=locale),
                    'type': location_type,
                    'product_name': '',
                    'product_id': line.product_id,
                    'product_uom': line.product_uom.name,

                    'product_uom_qty_in': product_uom_qty_in,
                    'product_uom_qty_out': product_uom_qty_out,
                    'cost_in':self.format_value(cost_in),
                    'cost_out': self.format_value(cost_out),
                    'total_cost': self.format_value(total_cost),
                    'reference': line.reference,
                    'location_id': line.location_id.name,
                    'location_dest_id': line.location_dest_id.name,
                })

            product_id = line.product_id.id
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'company_id': self.env.user.company_id,
            'currency':  self.env.user.company_id.currency_id,
            'date': format_date(self.env, data['form']['date'], lang_code=locale),
            'from_date':  format_date(self.env,data['form']['from_date'], lang_code=locale),
            'to_date':  format_date(self.env,data['form']['to_date'], lang_code=locale),
            'docs': docs,
            }


    def get_initial_balance(self, date,product_id,location):
        res = self.env['stock.move.line'].search([('product_id','=', product_id),('location_dest_id','=', location),('date','<',date)])
        if res:
            qty = 0.0
            for l in res:
                qty+=l.qty_done
            return qty
        else:
            return 0.0

    def get_closing_balance(self, date,product_id,location):

        res = self.env['stock.move.line'].search([('product_id','=', product_id),('location_dest_id','=', location),('date','<=',date)])
        if res:
            qty = 0.0
            for l in res:
                qty+=l.qty_done
            return qty

        else:
            return 0.0



    def format_value(self, value, currency=False):
        if self.env.context.get('no_format'):
            return value
        currency_id = currency or self.env.user.company_id.currency_id
        if currency_id.is_zero(value):
            # don't print -0.0 in reports
            value = abs(value)
        res = formatLang(self.env, value, currency_obj=currency_id)
        return res
