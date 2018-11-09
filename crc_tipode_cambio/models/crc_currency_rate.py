# -*- coding: utf-8 -*-
import requests
import datetime
import logging
import xml.etree.ElementTree as ET
from odoo import models, fields, api


_logger = logging.getLogger(__name__)

class crc_currency_rate(models.Model):
    #defining class attributes
    _name = 'crc_currency_rate'

    i = datetime.datetime.now()
    url = "http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/WebServices/wsIndicadoresEconomicos.asmx/ObtenerIndicadoresEconomicos?tcIndicador=318&tcFechaInicio="+str(i.day)+"/"+str(i.month)+"/"+str(i.year)+"&tcFechaFinal="+str(i.day)+"/"+str(i.month)+"/"+str(i.year)+"&tcNombre=Odoo&tnSubNiveles=S"
    name = fields.Char(string="Fecha")
    rate = fields.Float(string="Tipo de Cambio de Venta BCCR", store=True)
    data = fields.Binary(string='upload Certificate',attachment = True)


    def import_file(self):

        # your treatment
        return True

    #setting the fields in form
    @api.onchange('name')
    def _update_Currency_rate(self):
        #self.name = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}" or ''
        self.name = self.i.strftime("%Y-%m-%d %H:%M:%S")

    @api.multi
    def refresh_crc_currency(self):
        req = requests.get(self.url)
        root = ET.fromstring(req.text)
        for rec in self:
            try:
                for child in root.iter('NUM_VALOR'):
                    rec.rate = float(child.text)
                    rate_Model = rec.env['res.currency.rate']
                    rate_name = rec.env['res.currency.rate'].search([('currency_id', '=', 40)], limit=1).name
                    rate_id = rec.env['res.currency.rate'].search([('currency_id', '=', 40)], limit=1).id
                    #rate_date = f"{datetime.datetime.now():%Y-%m-%d}"
                    rate_date = self.i.strftime("%Y-%m-%d")
                    sql_param_rate = float(child.text)
                    company_ids = self.env['res.company'].sudo().search([])
                    if rate_date == rate_name :
                        for company in company_ids:
                            rec.env.cr.execute("UPDATE res_currency_rate SET rate = %s WHERE id = %s and company_id = %s;",(sql_param_rate,rate_id, company.id))
                            _logger.info('Botón actualizar presionado query: UPDATE res_currency_rate SET rate = %s WHERE id = %s;',sql_param_rate,rate_id)
                        break
                    else:

                        for company in company_ids:
                            vals = {
                                'currency_id': 40,
                                'rate': float(child.text),
                                'name': str(rec.i.year) +"-"+str(rec.i.month)+"-"+str(rec.i.day),
                                'company_id': company.id,
                            }
                            rate_Model.create(vals)
            except Exception as exc:
                _logger.error(repr(exc))
        return True
    

    @api.multi
    def run_update(self):
        self.refresh_crc_currency()

    #model fro the cron update tasks
    @api.model
    def _cron_update_CRC_Rate(self):
        _logger.info('Iniciando cron task')
        self._update_crc()
        _logger.info('Finalizando cron task')
        
    # function for the scheduled task
    @api.multi
    def _update_crc(self):
        req = requests.get(self.url)
        root = ET.fromstring(req.text)
        for child in root.iter('NUM_VALOR'):
            rate_Model = self.env['res.currency.rate']
            rate_name = self.env['res.currency.rate'].search([('currency_id', '=', 40)], limit=1).name
            rate_id = self.env['res.currency.rate'].search([('currency_id', '=', 40)], limit=1).id
            #rate_date = f"{datetime.datetime.now():%Y-%m-%d}"
            rate_date = self.i.strftime("%Y-%m-%d")
            sql_param_rate = float(child.text)
            company_ids = self.env['res.company'].sudo().search([])

            if rate_date == rate_name :
                for company in company_ids:
                    self.env.cr.execute("UPDATE res_currency_rate SET rate = %s WHERE id = %s and company_id = %s;",(sql_param_rate,rate_id, company.id))

                    _logger.info('Moneda CRC actualizada, método write, valor: %s', float(child.text))

                vals ={
                    'name' : self.i.strftime("%Y-%m-%d %H:%M:%S"),
                    'rate' : float(child.text)
                }
                self.create(vals)
                break
            else:
                for company in company_ids:
                    vals = {
                        'currency_id': 40,
                        'rate': float(child.text),
                        'name': str(self.i.year) +"-"+str(self.i.month)+"-"+str(self.i.day),
                        'company_id': company.id,
                    }
                    rate_Model.create(vals)

                _logger.info('Moneda CRC actualizada método crear, valor: %s',sql_param_rate)
                # vals2 ={
                #     'name' : f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}",
                #     'rate' : float(child.text)
                # }
                vals2 ={
                    'name' : self.i.strftime("%Y-%m-%d %H:%M:%S"),
                    'rate' : float(child.text)
                }
                self.create(vals2)