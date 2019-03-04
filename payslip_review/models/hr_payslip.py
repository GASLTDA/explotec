from odoo import models, fields, api
from datetime import datetime,date

class hr_payslip(models.Model):
    _inherit = 'hr.payslip'
    
    @api.model
    def employee_payslip_years(self):
        sql = """SELECT distinct EXTRACT(Year FROM hr_payslip.date_from) as year
            from hr_payslip"""
        self.env.cr.execute(sql)
        return self.env.cr.dictfetchall()
    
    @api.model
    def payslip_update_input(self,input_id,amount):
        amount = float(amount)
        input_id = int(input_id)
        paylslip_rule = self.env['hr.payslip.input'].browse(input_id)
        return paylslip_rule.write({'amount':amount})
    
    
    @api.model
    def employee_payslip_data(self,month,year,emp_id,batch):
        sql = """SELECT hr_payslip.id as line_id,resource_resource.name,hr_payslip.state,        
            array_to_string(array_agg(hr_payslip_line.salary_rule_id),',') as salary_line_rule_ids,
            array_to_string(array_agg(hr_payslip_line.total),',') as salary_line_totals,
            array_to_string(array_agg(hr_payslip_input.id),',') as salary_input_ids,
            array_to_string(array_agg(hr_payslip_input.code),',') as salary_input_codes,
            array_to_string(array_agg(coalesce(hr_payslip_input.amount,0)),',') as salary_input_amounts,
            EXTRACT(MONTH FROM hr_payslip.date_from) as month,EXTRACT(Year FROM hr_payslip.date_from) as year
            from hr_payslip
            left join hr_payslip_line on hr_payslip.id = hr_payslip_line.slip_id
            left join hr_payslip_input on hr_payslip.id = hr_payslip_input.payslip_id
            join hr_employee on hr_employee.id =  hr_payslip.employee_id
            left join resource_resource on resource_resource.id = hr_employee.resource_id
            where 1 = 1
            """
        if month > 0:
            sql += " and EXTRACT(MONTH FROM hr_payslip.date_from) =" + str(month)
        if year > 0:
            sql += " and EXTRACT(Year FROM hr_payslip.date_from) =" + str(year)
        if emp_id > 0:
            sql += " and hr_employee.id = " + str(emp_id)
        if batch > 0:
            sql += " and hr_payslip.payslip_run_id = " + str(batch)
        sql += """ group by hr_payslip.id,resource_resource.name,hr_payslip.state,payslip_run_id
            order by date_from desc,resource_resource.name"""
            
        self.env.cr.execute(sql)
        return self.env.cr.dictfetchall()
    
    @api.model
    def payslip_salary_data(self,month,year,emp_id,batch):
        salary_rules = self.env['hr.salary.rule'].search([], order='sequence')
        salary_inputs = self.env['hr.rule.input'].search([], order='id')
        
        
        month = int(month)
        year = int(year)
        emp_id = int(emp_id)
        batch = int(batch)
        res = self.employee_payslip_data(month,year,emp_id,batch)
        payslip_data = []
        header = {}
        rule_counter = 0
        header[rule_counter] = ['',0,'']
        rule_counter +=1
        header[rule_counter] = ['header',0,'']
        rule_counter +=1
        header[rule_counter] = ['header',0,'']
        rule_counter +=1
        header[rule_counter] = ['header',0,'Employee name']
        rule_counter +=1
        header[rule_counter] = ['header',0,'Month']
        rule_counter +=1
        header[rule_counter] = ['header',0,'Year']
        rule_counter +=1
        
        for _input in salary_inputs:
            header[rule_counter] = ['header',0,_input.name + ' (' + _input.code + ')']
            rule_counter+=1
        
        for _rule in salary_rules:
            header[rule_counter] = ['header',0,_rule.name]
            rule_counter+=1
        payslip_data.append(header)
        
        employee_counter = 1
        for rec in res:
            emp_data = {}
            line_id = rec["line_id"]
            emplyee_name = rec["name"]
            month = rec["month"]
            year = rec["year"]
            salary_line_rule_ids =  rec["salary_line_rule_ids"].split(',')
            salary_line_totals = rec["salary_line_totals"].split(',')
            
            salary_input_ids =  rec["salary_input_ids"].split(',')
            salary_input_codes = rec["salary_input_codes"].split(',')
            salary_input_amounts = rec["salary_input_amounts"].split(',')
            
            rule_counter = 0
            emp_data[rule_counter] = ['state',0,rec['state']]
            rule_counter +=1
            emp_data[rule_counter] = ['compute',0,line_id]
            rule_counter +=1
            emp_data[rule_counter] = ['confirm',0,line_id]
            rule_counter +=1
            emp_data[rule_counter] = ['info',0,emplyee_name]
            rule_counter +=1
            emp_data[rule_counter] = ['info',0,month]
            rule_counter +=1
            emp_data[rule_counter] = ['info',0,year]
            rule_counter +=1
            
            for _input in salary_inputs:
                rule_is_exist = False
                total_counter = 0
                for code in salary_input_codes:
                    if code and str(code) == str(_input.code):
                        rule_is_exist = True
                        emp_data[rule_counter] = ['input',str(salary_input_ids[total_counter]),str(salary_input_amounts[total_counter])]    
                    total_counter+=1
                if not rule_is_exist:
                    emp_data[rule_counter] = ['input',0,'-1']
                rule_counter+=1
            
            for salary_rule in salary_rules:
                rule_is_exist = False
                total_counter = 0
                for employee_rule in salary_line_rule_ids:
                    if employee_rule and int(employee_rule) == int(salary_rule.id):
                        rule_is_exist = True
                        emp_data[rule_counter] = ['rule',0,str(salary_line_totals[total_counter])]
                    total_counter+=1
                if not rule_is_exist:
                    emp_data[rule_counter] = ['rule',0,'-1']
                rule_counter+=1
            employee_counter+=1
            payslip_data.append(emp_data)
        
        
        footer = {}
        rule_counter = 0
        footer[rule_counter] = ['',0,'']
        rule_counter +=1
        footer[rule_counter] = ['footer',0,'']
        rule_counter +=1
        footer[rule_counter] = ['footer',0,'']
        rule_counter +=1
        footer[rule_counter] = ['footer',0,'']
        rule_counter +=1
        footer[rule_counter] = ['footer',0,'']
        rule_counter +=1
        footer[rule_counter] = ['footer',0,'']
        rule_counter +=1
        
        for _input in salary_inputs:
            footer[rule_counter] = ['footer footer_input',0,'']
            rule_counter+=1
        
        for _rule in salary_rules:
            footer[rule_counter] = ['footer',0,rule_counter - 1]
            rule_counter+=1
        payslip_data.append(footer)
            
        return payslip_data
