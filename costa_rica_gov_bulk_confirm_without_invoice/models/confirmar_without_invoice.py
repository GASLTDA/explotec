from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import time

import datetime

import base64

import re
import requests
import string

import xml.etree.ElementTree as ET


class ConfirmarInvoiceWizard(models.Model):
    _name = 'confirmar.without.invoice'
    _rec_name = 'date'

    state_invoice_partner = fields.Selection([('1', 'Aceptado'), ('3', 'Rechazado'), ('2', 'Aceptacion parcial')],
                                             'Respuesta del Cliente')
    terminal = fields.Many2one('terminal')
    date = fields.Date('Date')
    company_id = fields.Many2one('res.company')
    wizard_id = fields.Many2one('confirmar.wizard.without.invoice')
    xml_supplier_approval = fields.Binary(string="XML Proveedor", required=True, copy=False, attachment=True)
    sequence=fields.Integer(default=1)
    response = fields.Text(copy=False)
    response_xml = fields.Text(copy=False)
    haicenda_status = fields.Selection(
        [('procesando', 'Procesando'), ('aceptado', 'Aceptado'), ('rechazado', 'Rechazado'),
         ('aceptación parcial', 'Aceptación parcial')], default="rechazado", copy=False, string='Hacienda Status')

    @api.multi
    def charge_xml_data(self):

        root = ET.fromstring(re.sub(' xmlns="[^"]+"', '', base64.b64decode(self.xml_supplier_approval).decode(),
                                    count=1))  # quita el namespace de los elementos
        self.clave_numerica = root.findall('Clave')[0].text
        self.date = root.findall('FechaEmision')[0].text

    @api.multi
    def send_xml(self):
        invoice_dict = ''
        for id in self:
            if id.xml_supplier_approval:
                root = ET.fromstring(
                    re.sub(' xmlns="[^"]+"', '', base64.b64decode(id.xml_supplier_approval).decode(), count=1))

                if not id.state_invoice_partner:
                    raise UserError('Debe primero seleccionar el tipo de respuesta para el archivo cargado.')
                # if float(root.findall('ResumenFactura')[0].findall('TotalComprobante')[0].text) == id.amount_total:
                if True:
                    if id.state_invoice_partner:
                        if id.state_invoice_partner == '1':
                            detalle_mensaje = 'Aceptado'
                            type = "05"
                        if id.state_invoice_partner == '2':
                            detalle_mensaje = 'Aceptado parcial'
                            type = "06"
                        if id.state_invoice_partner == '3':
                            detalle_mensaje = 'Rechazado'
                            type = "07"
                        invoice_dict += '[root][Clave]' + root.findall('Clave')[0].text + '[|Clave]'
                        NumeroConsecutivo = str(id.company_id.store_branch) + id.terminal.name + type + str(int(time.time()))[:10]

                        invoice_dict += '[NumeroCedulaEmisor]' + str(
                            root.findall('Emisor')[0].findall('Identificacion')[0].findall('Numero')[0].text).zfill(
                            12) + '[|NumeroCedulaEmisor]'
                        invoice_dict += '[FechaEmisionDoc]' + root.findall('FechaEmision')[
                            0].text + '[|FechaEmisionDoc]'
                        invoice_dict += '[Mensaje]' + id.state_invoice_partner + '[|Mensaje]'
                        invoice_dict += '[DetalleMensaje]' + detalle_mensaje + '[|DetalleMensaje]'
                        if len(root.findall('ResumenFactura')[0].findall('TotalImpuesto')) > 0:
                            invoice_dict += '[MontoTotalImpuesto]' + \
                                            root.findall('ResumenFactura')[0].findall('TotalImpuesto')[
                                                0].text + '[|MontoTotalImpuesto]'
                        else:
                            invoice_dict += '[MontoTotalImpuesto]' + '0.0' + '[|MontoTotalImpuesto]'

                        invoice_dict += '[TotalFactura]' + \
                                        root.findall('ResumenFactura')[0].findall('TotalComprobante')[
                                            0].text + '[|TotalFactura]'
                        invoice_dict += '[NumeroCedulaReceptor]' + str(
                            root.findall('Receptor')[0].findall('Identificacion')[0].findall('Numero')[0].text).zfill(
                            12) + '[|NumeroCedulaReceptor]'
                        invoice_dict += '[NumeroConsecutivoReceptor]' + NumeroConsecutivo + '[|NumeroConsecutivoReceptor]'

            invoice_dict += '[|root]'

            try:
                url = id.company_id.url + '/api/hacienda'

                res = requests.post(url, {
                    'data': base64.b64encode(invoice_dict.encode()),
                    'key': id.company_id.access_token,
                    'clave': root.findall('Clave')[0].text,
                    'fecha': root.findall('FechaEmision')[0].text,
                    'type': type,
                    'date': str(id.date),
                    'vat': id.company_id.company_registry,
                    'emisor': json.dumps({
                        'tipoIdentificacion': root.findall('Emisor')[0].findall('Identificacion')[0].findall('Numero')[
                            0].text,
                        'numeroIdentificacion': root.findall('Emisor')[0].findall('Nombre')[0].text
                    }),
                    'receptor': json.dumps({
                        'tipoIdentificacion': id.company_id.partner_id.tipo,
                        'numeroIdentificacion': id.company_id.company_registry
                    })
                })
                try:
                    res = json.loads(res.content.decode())
                    message = res['message'].strip('\n')

                    id.response = res
                    message = json.loads(message)
                    if 'ind-estado' in message:
                        id.haicenda_status = message['ind-estado']
                    if 'respuesta-xml' in message:
                        id.response_xml = base64.b64decode(message['respuesta-xml'])
                except:
                    id.response = res

            except requests.exceptions.RequestException:
                raise UserError(_('Algo salió mal, intente de nuevo más tarde'))

            except requests.exceptions.HTTPError:
                raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
            except requests.exceptions.ConnectionError:
                raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
            except requests.exceptions.Timeout:
                raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
                # else:
                #     raise UserError('Error!.\nEl monto total de la factura no coincide con el monto total del archivo XML')


    @api.onchange('xml_supplier_approval')
    def _onchange_xml_supplier_approval(self):
        if self.xml_supplier_approval:
            root = ET.fromstring(re.sub(' xmlns="[^"]+"', '', base64.b64decode(self.xml_supplier_approval).decode(),
                                        count=1))  # quita el namespace de los elementos
            if not root.findall('Clave'):
                return {'value': {'xml_supplier_approval': False}, 'warning': {'title': 'Atención',
                                                                               'message': 'El archivo xml no contiene el nodo Clave. Por favor cargue un archivo con el formato correcto.'}}
            if not root.findall('FechaEmision'):
                return {'value': {'xml_supplier_approval': False}, 'warning': {'title': 'Atención',
                                                                               'message': 'El archivo xml no contiene el nodo FechaEmision. Por favor cargue un archivo con el formato correcto.'}}
            if not root.findall('Emisor'):
                return {'value': {'xml_supplier_approval': False}, 'warning': {'title': 'Atención',
                                                                               'message': 'El archivo xml no contiene el nodo Emisor. Por favor cargue un archivo con el formato correcto.'}}
            if not root.findall('Emisor')[0].findall('Identificacion'):
                return {'value': {'xml_supplier_approval': False}, 'warning': {'title': 'Atención',
                                                                               'message': 'El archivo xml no contiene el nodo Identificacion. Por favor cargue un archivo con el formato correcto.'}}
            if not root.findall('Emisor')[0].findall('Identificacion')[0].findall('Tipo'):
                return {'value': {'xml_supplier_approval': False}, 'warning': {'title': 'Atención',
                                                                               'message': 'El archivo xml no contiene el nodo Tipo. Por favor cargue un archivo con el formato correcto.'}}
            if not root.findall('Emisor')[0].findall('Identificacion')[0].findall('Numero'):
                return {'value': {'xml_supplier_approval': False}, 'warning': {'title': 'Atención',
                                                                               'message': 'El archivo xml no contiene el nodo Numero. Por favor cargue un archivo con el formato correcto.'}}
            # if not (root.findall('ResumenFactura') and root.findall('ResumenFactura')[0].findall('TotalImpuesto')):
            #     return {'value': {'xml_supplier_approval': False},'warning': {'title': 'Atención','message': 'No se puede localizar el nodo TotalImpuesto. Por favor cargue un archivo con el formato correcto.'}}
            if not (root.findall('ResumenFactura') and root.findall('ResumenFactura')[0].findall('TotalComprobante')):
                return {'value': {'xml_supplier_approval': False}, 'warning': {'title': 'Atención',
                                                                               'message': 'No se puede localizar el nodo TotalComprobante. Por favor cargue un archivo con el formato correcto.'}}

    @api.multi
    def _auto_status_check_supplier(self):
        ids = self.env['confirmar.without.invoice'].search([('haicenda_status','in',['procesando','rechazado'])])

        for id in ids:
            if id.company_id.electronic_invoice:
                id.response = ''
                id.response_xml = ''
                id.send_xml()
