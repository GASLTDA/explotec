# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from dateutil.relativedelta import *
from odoo.exceptions import ValidationError
from odoo.tools import format_date,formatLang
from odoo.exceptions import UserError
import xlsxwriter
import base64


class StockMovementWizard(models.TransientModel):
    _name = 'stock.movement.wizard'

    name = fields.Selection([('today','Today'),('this_month','This Month'),('selected_date','Selected Date'),('date_range','Date Range')],string='Type', default='today')
    date = fields.Date()
    from_date = fields.Date()
    to_date = fields.Date()
    file = fields.Binary()
    file_name = fields.Char()

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


    @api.multi
    def print_excel(self):
        if self.name == 'selected_date':
            if self.date == False:
                raise UserError("Please select the date")
        if self.name == 'date_range':
            if self.from_date == False or self.to_date == False:
                raise UserError("Please select the date")

        type = self.name
        date = self.date
        from_date = self.from_date
        to_date = self.to_date

        domain = [('company_id','=',self.env.user.company_id.id)]
        if type == 'today':
            domain += [('date','>=',date + ' '+'00:00:00'),('date','<=',date + ' '+'23:59:59'),('state','=','done')]
        elif type == 'this_month':
            domain += [('date','>=',from_date + ' '+'00:00:00'),('date','<=',to_date + ' '+'23:59:59'),('state','=','done')]
        elif type == 'selected_date':
            domain += [('date','>=',date + ' '+'00:00:00'),('date','<=',date + ' '+'23:59:59'),('state','=','done')]
        elif type == 'date_range':
            domain += [('date','>=',from_date + ' '+'00:00:00'),('date','<=',to_date + ' '+'23:59:59'),('state','=','done')]

        locale = self._context.get('lang') or 'en_US'
        self.file_name = 'stock_movement_' + self.from_date + '_' + self.to_date + '.xls'
        workbook = xlsxwriter.Workbook(self.file_name)

        # Cell & Sheet formatting
        sheet = workbook.add_worksheet('Stock Movement')
        title_format = workbook.add_format({'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter',
                                            'fg_color': '#ededed'})
        title_format1 = workbook.add_format({'bold': 1, 'border': 1, 'align': 'right', 'valign': 'vcenter'})
        border = workbook.add_format({'border': 1})
        border_number = workbook.add_format({'border': 1, 'align': 'right'})

        # Report Title
        sheet.merge_range('A1:J1', 'Stock Movement', title_format)
        if self.from_date and self.to_date:
            sheet.merge_range('A2:J2',
                          '{} (From: {} - To: {})'.format(self.env.user.company_id.name,format_date(self.env, value=self.from_date, lang_code=locale),
                                                          format_date(self.env, value=self.to_date, lang_code=locale)),title_format1)
        if self.date:
            sheet.merge_range('A2:J2',
                  '{} (Date: {})'.format(self.env.user.company_id.name,format_date(self.env, value=self.date, lang_code=locale)),title_format1)
        # Setting Column Widths
        sheet.set_column('A:A', 70)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 70)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 20)
        sheet.set_column('I:I', 20)
        sheet.set_column('J:J', 20)

        # Report Headers
        sheet.write('A3', 'Date', title_format)
        sheet.write('B3', 'Type', title_format)
        sheet.write('C3', 'Reference', title_format)
        sheet.write('D3', 'Source Location', title_format)
        sheet.write('E3', 'Destination Location', title_format)
        sheet.write('F3', 'In', title_format)
        sheet.write('G3', 'Out', title_format)
        sheet.write('H3', 'Cost In', title_format)
        sheet.write('I3', 'Cost Out', title_format)
        sheet.write('J3', 'Total Cost', title_format)

        move_lines = self.env['stock.move'].sudo().search(domain, order='product_id, date asc')
        locale = self._context.get('lang') or 'en_US'
        product_id = None
        line_date = None
        line_dest = None
        old_location_type = None
        row = 4
        for line in move_lines:
            dest_usage = line.location_dest_id.usage
            src_usage =line.location_id.usage
            if dest_usage == 'internal' and src_usage == 'internal':
                location_type='Internal Transfer'
            elif dest_usage == 'vendor':
                location_type='Purchase Return'
            elif dest_usage == 'customer':
                location_type='Sale'
            elif dest_usage == 'production':
                location_type = 'Raw Material'
            elif src_usage == 'production' and dest_usage == 'internal':
                location_type = 'Finished Product'
            elif src_usage == 'vendor' and dest_usage == 'internal':
                location_type = 'Purchase'
            elif src_usage == 'customer' and dest_usage == 'internal':
                location_type = 'Sales Return'
            else:
                location_type = 'Internal Transfer'

            if product_id != line.product_id.id:
                if product_id != None:
                    row +=1
                    sheet.write('A'+str(row), '', title_format1)
                    sheet.write('B'+str(row), '', title_format1)
                    sheet.write('C'+str(row), '', title_format1)
                    sheet.write('D'+str(row), '', title_format1)
                    sheet.write('E'+str(row), 'CLOSING BALANCE', title_format1)
                    sheet.write('F'+str(row), '', title_format1)
                    sheet.write('G'+str(row), self.get_closing_balance(date or to_date,product_id, line_dest.id), title_format1)
                    sheet.write('H'+str(row), '', title_format1)
                    sheet.write('I'+str(row), '', title_format1)
                    sheet.write('J'+str(row), '', title_format1)
                    row +=1

                if True:
                    row += 1
                    item_name = line.product_id.name
                    if line.product_id.product_tmpl_id.x_studio_field_5iBe0 != False:
                        item_name += ' ('+line.product_id.product_tmpl_id.x_studio_field_5iBe0+') '
                    sheet.write('A'+str(row), item_name, title_format)
                    sheet.write('B'+str(row), '', title_format)
                    sheet.write('C'+str(row), '', title_format)
                    sheet.write('D'+str(row), '', title_format)
                    sheet.write('E'+str(row), '', title_format)
                    sheet.write('F'+str(row), '', title_format)
                    sheet.write('G'+str(row), '', title_format)
                    sheet.write('H'+str(row), '', title_format)
                    sheet.write('I'+str(row), '', title_format)
                    sheet.write('J'+str(row), '', title_format)

                    row += 1
                    sheet.write('A'+str(row), '', title_format1)
                    sheet.write('B'+str(row), '', title_format1)
                    sheet.write('C'+str(row), '', title_format1)
                    sheet.write('D'+str(row), '', title_format1)
                    sheet.write('E'+str(row), 'BEGINNING BALANCE', title_format1)
                    sheet.write('F'+str(row), self.get_initial_balance(date or from_date,line.product_id.id, line.location_dest_id.id) , title_format1)
                    sheet.write('G'+str(row), '', title_format1)
                    sheet.write('H'+str(row), '', title_format1)
                    sheet.write('I'+str(row), '', title_format1)
                    sheet.write('J'+str(row), '', title_format1)


            product_uom_qty_out = 0.0
            product_uom_qty_in = 0.0
            cost_in = 0.0
            cost_out = 0.0
            total_cost = 0.0
            if location_type =='Internal Transfer':
                product_uom_qty_in  = line.product_uom_qty
                product_uom_qty_out  = 0.0
                cost_in  = 0.0
                cost_out  = 0.0
                total_cost = 0.0
            elif location_type == 'Sale':
                product_uom_qty_in  = 0.0
                product_uom_qty_out  = line.product_uom_qty
                cost_in  = line.product_id.standard_price
                total_cost  = line.product_uom_qty * line.product_id.standard_price
                cost_out  = 0.0

            elif location_type == 'Purchase':
                product_uom_qty_in  = line.product_uom_qty
                product_uom_qty_out  = 0.0
                cost_in  = 0.0
                cost_out = line.product_id.standard_price
                total_cost = line.product_uom_qty * line.product_id.standard_price

            elif location_type == 'Raw Material':
                product_uom_qty_in  = 0.0
                product_uom_qty_out  = line.product_uom_qty
                cost_in = 0.0
                cost_out = 0.0
                total_cost = 0.0

            elif location_type == 'Finished Product':
                product_uom_qty_in  = line.product_uom_qty
                product_uom_qty_out  = 0.0
                cost_in = 0.0
                cost_out = 0.0
                total_cost = 0.0

            elif location_type == 'Purchase Return':
                product_uom_qty_in  = 0.0
                product_uom_qty_out  = line.product_uom_qty
                cost_in  = line.product_id.standard_price
                total_cost  = line.product_uom_qty * line.product_id.standard_price
                cost_out  = 0.0

            elif location_type == 'Sales Return':
                product_uom_qty_in  = line.product_uom_qty
                product_uom_qty_out  = 0.0
                cost_in  = 0.0
                cost_out = line.product_id.standard_price
                total_cost = line.product_uom_qty * line.product_id.standard_price

            row += 1
            sheet.write('A'+str(row), format_date(self.env,line.date, lang_code=locale), border)
            sheet.write('B'+str(row),location_type , border)
            sheet.write('C'+str(row),line.reference , border)
            sheet.write('D'+str(row),line.location_id.name, border)
            sheet.write('E'+str(row),line.location_dest_id.name , border)
            sheet.write('F'+str(row),product_uom_qty_in, border_number)
            sheet.write('G'+str(row),product_uom_qty_out, border_number)
            sheet.write('H'+str(row), self.format_value(cost_in), border_number)
            sheet.write('I'+str(row), self.format_value(cost_out), border_number)
            sheet.write('J'+str(row),self.format_value(total_cost), border_number)


            product_id = line.product_id.id
            line_date = line.date
            line_dest = line.location_dest_id
            old_location_type = location_type

        if product_id != None:
            row +=1
            sheet.write('A'+str(row), '', title_format1)
            sheet.write('B'+str(row), '', title_format1)
            sheet.write('C'+str(row), '', title_format1)
            sheet.write('D'+str(row), '', title_format1)
            sheet.write('E'+str(row), 'CLOSING BALANCE', title_format1)
            sheet.write('F'+str(row), '', title_format1)
            sheet.write('G'+str(row), self.get_closing_balance(date or to_date,product_id, line_dest.id), title_format1)
            sheet.write('H'+str(row), '', title_format1)
            sheet.write('I'+str(row), '', title_format1)
            sheet.write('J'+str(row), '', title_format1)
            row +=1
            sheet.write('A'+str(row), '', border)
            sheet.write('B'+str(row), '', border)
            sheet.write('C'+str(row), '', border)
            sheet.write('D'+str(row), '', border)
            sheet.write('E'+str(row), '', border)
            sheet.write('F'+str(row), '', border)
            sheet.write('G'+str(row), '', border)
            sheet.write('H'+str(row), '', border)
            sheet.write('I'+str(row), '', border)
            sheet.write('J'+str(row), '', border)
        workbook.close()

        result_file = open(self.file_name, 'rb').read()
        self.file =base64.encodebytes(result_file)


        return {
            'name': 'Report',
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=" + self._name +"&id=" + str(
                self.id) + "&filename_field="+self.file_name+"&field=file&download=true&filename=" + self.file_name ,
            'target': 'self',
        }




    def get_initial_balance(self, date,product_id,location):
        self.env.context = {'to_date':date, 'company_owned':True}
        res = self.env['product.product'].sudo().search([('id','=', product_id)])
        if res:
            qty = 0.0
            for l in res:
                qty += l.qty_available

            return qty
        else:
            return 0.0

    def get_closing_balance(self, date,product_id,location):
        self.env.context = {'to_date':date, 'company_owned':True}
        res = self.env['product.product'].sudo().search([('id','=', product_id)])
        if res:
            qty = 0.0
            for l in res:
                qty += l.qty_available

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
        move_lines = self.env['stock.move'].sudo().search(domain, order='product_id, date asc')
        locale = self._context.get('lang') or 'en_US'
        product_id = None
        line_date = None
        line_dest = None
        old_location_type = None

        for line in move_lines:
            dest_usage = line.location_dest_id.usage
            src_usage =line.location_id.usage
            if dest_usage == 'internal' and src_usage == 'internal':
                location_type='Internal Transfer'
            elif dest_usage == 'vendor':
                location_type='Purchase Return'
            elif dest_usage == 'customer':
                location_type='Sale'
            elif dest_usage == 'production':
                location_type = 'Raw Material'
            elif src_usage == 'production' and dest_usage == 'internal':
                location_type = 'Finished Product'
            elif src_usage == 'vendor' and dest_usage == 'internal':
                location_type = 'Purchase'
            elif src_usage == 'customer' and dest_usage == 'internal':
                location_type = 'Sales Return'
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
                                  'product_uom_qty_out': self.get_closing_balance(date or to_date,product_id, line_dest.id),
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

                if True:

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
                    item_name = line.product_id.name
                    if line.product_id.product_tmpl_id.x_studio_field_5iBe0 != False:
                        item_name += ' ('+line.product_id.product_tmpl_id.x_studio_field_5iBe0+') '

                    docs.append({ 'date': '<b>Item: ' + item_name + '</b>',
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
                        'product_uom_qty_in':self.get_initial_balance(date or from_date,line.product_id.id, line.location_dest_id.id),
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
                product_uom_qty_in  = line.product_uom_qty
                product_uom_qty_out  = 0.0
                cost_in  = 0.0
                cost_out  = 0.0
                total_cost = 0.0
            elif location_type == 'Sale':
                product_uom_qty_in  = 0.0
                product_uom_qty_out  = line.product_uom_qty
                cost_in  = line.product_id.standard_price
                total_cost  = line.product_uom_qty * line.product_id.standard_price
                cost_out  = 0.0

            elif location_type == 'Purchase':
                product_uom_qty_in  = line.product_uom_qty
                product_uom_qty_out  = 0.0
                cost_in  = 0.0
                cost_out = line.product_id.standard_price
                total_cost = line.product_uom_qty * line.product_id.standard_price

            elif location_type == 'Raw Material':
                product_uom_qty_in  = 0.0
                product_uom_qty_out  = line.product_uom_qty
                cost_in = 0.0
                cost_out = 0.0
                total_cost = 0.0

            elif location_type == 'Finished Product':
                product_uom_qty_in  = line.product_uom_qty
                product_uom_qty_out  = 0.0
                cost_in = 0.0
                cost_out = 0.0
                total_cost = 0.0

            elif location_type == 'Purchase Return':
                product_uom_qty_in  = 0.0
                product_uom_qty_out  = line.product_uom_qty
                cost_in  = line.product_id.standard_price
                total_cost  = line.product_uom_qty * line.product_id.standard_price
                cost_out  = 0.0

            elif location_type == 'Sales Return':
                product_uom_qty_in  = line.product_uom_qty
                product_uom_qty_out  = 0.0
                cost_in  = 0.0
                cost_out = line.product_id.standard_price
                total_cost = line.product_uom_qty * line.product_id.standard_price

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
            line_date = line.date
            line_dest = line.location_dest_id
            old_location_type = location_type

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
                          'product_uom_qty_out': self.get_closing_balance(date or to_date,product_id, line_dest.id),
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
        self.env.context = {'to_date':date, 'company_owned':True}
        res = self.env['product.product'].sudo().search([('id','=', product_id)])
        if res:
            qty = 0.0
            for l in res:
                qty += l.qty_available

            return qty
        else:
            return 0.0

    def get_closing_balance(self, date,product_id,location):
        self.env.context = {'to_date':date, 'company_owned':True}
        res = self.env['product.product'].sudo().search([('id','=', product_id)])
        if res:
            qty = 0.0
            for l in res:
                qty += l.qty_available

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
