import json
import time

import datetime

import base64

import re
import requests
import string

import xml.etree.ElementTree as ET

from odoo import models, fields, api, _

from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _show_button(self):
        if self.type in ('out_invoice', 'out_refund') and self.company_id.electronic_invoice:
            if (self.state == 'open' or self.state == 'paid') and self.haicenda_status in (
            'procesando', 'rechazado', 'aceptación parcial'):
                self.show_button = True
            else:
                self.show_button = False
        else:
            self.show_button = False

    def _show_submit_button(self):
        if self.type in ('out_invoice', 'out_refund') and self.company_id.electronic_invoice:
            if (self.state == 'open' or self.state == 'paid') and self.haicenda_status in (
            'rechazado', 'aceptación parcial'):
                self.show_submit_button = True
            else:
                self.show_submit_button = False
        else:
            self.show_submit_button = False

    clave_numerica = fields.Char(_('Clave Numerica'), copy=False)

    request_datetime = fields.Char(copy=False)
    date = fields.Char(_('Date'), copy=False)
    response = fields.Text(copy=False)
    response_xml = fields.Text(copy=False)
    show_button = fields.Boolean(compute='_show_button')
    show_submit_button = fields.Boolean(compute='_show_submit_button')
    haicenda_status = fields.Selection(
        [('procesando', 'Procesando'), ('aceptado', 'Aceptado'), ('rechazado', 'Rechazado'),
         ('aceptación parcial', 'Aceptación parcial')], default="rechazado", copy=False, string='Hacienda Status')
    sale_condition = fields.Selection([
        ('01', 'Contado'),
        ('02', 'Crédito'),
        ('03', 'Consignación'),
        ('04', 'Apartado'),
        ('05', 'Arrendamiento con opción de compra'),
        ('06', 'Arrendamiento en función financiera'),
        ('99', 'Otros (se debe indicar la condición de la venta)')
    ], string=_('Condicion Venta'))

    payment_method = fields.Selection([
        ('01', 'Efectivo'),
        ('02', 'Tarjeta'),
        ('03', 'Cheque'),
        ('04', 'Transferencia – depósito bancario'),
        ('05', 'Recaudado por terceros'),
        ('99', 'Otros (se debe indicar el medio de pago)'),
    ], string=_('Medio Pago'))

    terminal = fields.Many2one('terminal')
    xml_file = fields.Binary(copy=False)
    submit_tries = fields.Integer(default=0)
    status_tries = fields.Integer(default=0)
    electronic_invoice = fields.Boolean(related='company_id.electronic_invoice')
    folio = fields.Char(_('Folio'), copy=False)
    pdf_sync = fields.Boolean(default=False, copy=False)

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        if self.company_id.electronic_invoice:
            if self.type in ('out_refund','out_invoice'):
                return self.generate_xml_file()
        return res

    @api.multi
    def _auto_pdf_submit(self):
        ids = self.env['account.invoice'].search([('haicenda_status','=','aceptado'),('pdf_sync','=', False)])
        for id in ids:
            self._cr.execute("SELECT id FROM ir_attachment WHERE res_id=%s AND res_model='account.invoice' AND mimetype='application/pdf'",[id.id])
            pdf = self._cr.fetchone()
            if pdf:
                pdf_file = self.env['ir.attachment'].sudo().browse(pdf[0])
                if pdf_file:
                    try:
                        res = requests.post(id.company_id.url + '/api/pdf', {
                            'data': pdf_file.datas,
                            'key': id.company_id.access_token,
                            'clave': id.clave_numerica,
                            'vat': id.company_id.company_registry,
                            'date': str(id.date_invoice),
                        })
                        try:
                            res = json.loads(res.content.decode())
                            if 'status' in res:
                                if res['status'] == 'Success':
                                    id.pdf_sync = True
                        except:
                            pass
                    except:
                        pass

        return True

    @api.multi
    def _auto_resubmit(self):
        ids = self.env['account.invoice'].search([('haicenda_status','in',('rechazado','aceptación parcial')),('state','not in',('draft','cancel')),('submit_tries','<=','10')])

        for id in ids:
            if id.company_id.electronic_invoice:
                if id.type in ('out_refund','out_invoice'):
                    id.response = ''
                    id.response_xml = ''
                    id.generate_xml_file(cron=True)
                    id.submit_tries = id.submit_tries+1

    @api.multi
    def _auto_status_check(self):
        ids = self.env['account.invoice'].search([('haicenda_status','=','procesando'),('state','not in',('draft','cancel')),('status_tries','<=','10')])

        for id in ids:
            if id.company_id.electronic_invoice:
                if id.type in ('out_refund','out_invoice'):
                    id.response = ''
                    id.response_xml = ''
                    id.check_status(True)
                    id.status_tries = id.status_tries+1

    @api.multi
    def check_status(self, cron = False):
        id = self

        if id.clave_numerica == False:
            raise UserError(_('Por favor envíe a Haicenda'))
        try:
            res = requests.post(id.company_id.url + '/api/hacienda/status', {
                'key': id.company_id.access_token,
                'clave': id.clave_numerica,

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
                if 'fecha' in message:
                    id.request_datetime = message['fecha']

                if id.haicenda_status == 'aceptado':

                    file = requests.post(id.company_id.url + '/api/download_xml', {
                        'key': id.company_id.access_token,
                        'clave': id.clave_numerica,
                        'vat': id.company_id.company_registry,
                        'date': str(id.date_invoice),
                    })

                    file = json.loads(file.content.decode())

                    if file['status'] == 'Success':
                        xml_file = file['message']
                        id.xml_file = xml_file

            except:
                id.response = res

        except requests.exceptions.RequestException:
            if not cron:
                raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
            else:
                pass
        except requests.exceptions.HTTPError:
            if not cron:
                raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
            else:
                pass
        except requests.exceptions.ConnectionError:
            if not cron:
                raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
            else:
                pass
        except requests.exceptions.Timeout:
            if not cron:
                raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
            else:
                pass

    @api.multi
    def download_xml(self):
        for id in self:
            if id.haicenda_status == 'aceptado':
                try:
                    res = requests.post(id.company_id.url + '/api/download_xml', {
                        'key': id.company_id.access_token,
                        'clave': id.clave_numerica,
                        'vat': id.company_id.company_registry,
                        'date': str(id.date_invoice),
                    })

                    id.xml_file = res.content
                    return {
                            'name': 'Report',
                            'type': 'ir.actions.act_url',
                            'url': "web/content/?model=" + self._name +"&id=" + str(
                                id.id) + "&filename_field=file_name&field=xml_file&download=true&filename=" + id.clave_numerica +'.xml',
                            'target': 'self',
                    }
                except requests.exceptions.RequestException:
                    raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
                except requests.exceptions.HTTPError:
                    raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
                except requests.exceptions.ConnectionError:
                    raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
                except requests.exceptions.Timeout:
                    raise UserError(_('Algo salió mal, intente de nuevo más tarde'))


    @api.multi
    def generate_xml_file(self, model='account.invoice',cron=False):
        active_ids = self
        TotalDescuentos = 0.0
        for active_id in active_ids:
            id = active_id
            round_curr = id.currency_id.round

            invoice_dict = ''
            if id.type not in ('in_refund', 'out_invoice', 'out_refund'):
                return

            if id.number and len(id.number) <= 10 and id.number.isdigit():
                pass
            else:
                raise UserError(_(
                    'Los datos requeridos faltan o están vacíos. Verifique si la factura está validada. Verifique la secuencia de la factura no.'))

            if id.type == 'out_invoice':
                type = '01'
            elif id.type == 'in_refund':
                type = '02'  # Debit note (Vendor)
            elif id.type == 'out_refund':
                type = '03'  # Credit note (Customer)
            else:
                type = '01'

            # NumeroConsecutivo = '001' + '00001' + '01' + id.number
            NumeroConsecutivo = str(id.company_id.store_branch) + id.terminal.name + type + str(id.number)
            id.folio = NumeroConsecutivo
            date_time = datetime.datetime.strptime(id.date_invoice, '%Y-%m-%d')
            company_registry = id.company_id.company_registry
            if len(id.company_id.company_registry) < 12:

                diff = 12 - len(id.company_id.company_registry)
                i = 0
                while i < diff:
                    company_registry = "0" + company_registry
                    i += 1
            else:
                company_registry = id.company_id.company_registry

            Clave = '506' + date_time.strftime('%d%m%y') + company_registry + NumeroConsecutivo + '1' + str(
                time.time())[:8]
            FechaEmision = self.get_costa_date_time_with_t(datetime.datetime.now())

            invoice_dict += '[root][Clave]' + Clave + '[|Clave]'
            invoice_dict += '[NumeroConsecutivo]' + NumeroConsecutivo + '[|NumeroConsecutivo]'
            invoice_dict += '[FechaEmision]' + FechaEmision[:25] + '[|FechaEmision]'

            Emisor = '[Emisor][Nombre]' + id.company_id.name + '[|Nombre]'
            Emisor += '[Identificacion][Tipo]' + id.company_id.partner_id.tipo + '[|Tipo][Numero]' + str(id.company_id.company_registry).replace('-','').replace(' ','') + '[|Numero][|Identificacion]'
            Emisor += '[Ubicacion]'
            Emisor += '[Provincia]' + self._get_string(id.company_id.province_id.code) + '[|Provincia]'
            Emisor += '[Canton]' + self._get_string(id.company_id.canton_id.code).zfill(2) + '[|Canton]'
            Emisor += '[Distrito]' + self._get_string(id.company_id.district_id.code).zfill(2) + '[|Distrito]'
            Emisor += '[Barrio]' + self._get_string(id.company_id.district_id.code).zfill(2) + '[|Barrio]'
            Emisor += '[OtrasSenas]' + self._get_full_address(id.company_id) + '[|OtrasSenas]'
            Emisor += '[|Ubicacion]'

            if id.company_id.phone:
                Emisor += '[Telefono][CodigoPais]506[|CodigoPais][NumTelefono]' + str(id.company_id.phone).replace('-','').replace(' ','').replace('+','') + '[|NumTelefono][|Telefono]'

            Emisor += '[CorreoElectronico]' + id.company_id.email + '[|CorreoElectronico][|Emisor]'
            invoice_dict += Emisor

            Receptor = '[Receptor][Nombre]' + id.partner_id.name + '[|Nombre]'
            Receptor += '[Identificacion][Tipo]' + id.partner_id.tipo + '[|Tipo][Numero]' + str(id.partner_id.vat).replace('-','').replace(' ','') + '[|Numero][|Identificacion]'
            if id.partner_id.province_id and id.partner_id.canton_id and id.partner_id.district_id and id.partner_id.locality_id:
                Receptor += '[Ubicacion]'
                Receptor += '[Provincia]' + self._get_string(id.partner_id.province_id.code) + '[|Provincia]'
                Receptor += '[Canton]' + self._get_string(id.partner_id.canton_id.code).zfill(2) + '[|Canton]'
                Receptor += '[Distrito]' + self._get_string(id.partner_id.district_id.code).zfill(2) + '[|Distrito]'
                Receptor += '[Barrio]' + self._get_string(id.partner_id.locality_id.code).zfill(2) + '[|Barrio]'
                Receptor += '[OtrasSenas]' + self._get_full_address(id.partner_id) + '[|OtrasSenas]'
                Receptor += '[|Ubicacion]'
            Receptor += '[CorreoElectronico]' + id.partner_id.email + '[|CorreoElectronico][|Receptor]'

            invoice_dict += Receptor
            invoice_dict += '[CondicionVenta]' + id.sale_condition + '[|CondicionVenta]'
            invoice_dict += '[PlazoCredito]' + id.payment_term_id.name[:10] + '[|PlazoCredito]'
            invoice_dict += '[MedioPago]' + id.payment_method + '[|MedioPago]'

            DetalleServicio = ''

            LineaDetalle = ''
            total_lines = 0
            for line in id.invoice_line_ids:
                total_lines += 1
                LineaDetalle += '[LineaDetalle]'
                LineaDetalle += '[NumeroLinea]' + str(total_lines) + '[|NumeroLinea]'
                LineaDetalle += '[Codigo][Tipo]04[|Tipo][Codigo]' + str(
                    line.product_id.default_code or '000') + '[|Codigo][|Codigo]'
                LineaDetalle += '[Cantidad]' + str('%016.3F' % line.quantity) + '[|Cantidad]'
                LineaDetalle += '[UnidadMedida]' + str(line.uom_id.code or 'Unid') + '[|UnidadMedida]'
                LineaDetalle += '[Detalle]' + str(line.name).strip('\n').replace('[','(').replace(']',')').replace('|','')[:160] + '[|Detalle]'
                LineaDetalle += '[PrecioUnitario]' + str('%023.5f' % line.price_unit) + '[|PrecioUnitario]'
                LineaDetalle += '[MontoTotal]' + str('%023.5f' % (line.quantity * line.price_unit)) + '[|MontoTotal]'

                if line.discount > 0.0:
                    line_total_without_dis = 0.0
                    line_total_without_dis = line.quantity * line.price_unit
                    discount_txt = line_total_without_dis * (line.discount / 100)
                    TotalDescuentos += discount_txt
                    LineaDetalle += '[MontoDescuento]' + str(round_curr(discount_txt)) + '[|MontoDescuento]'
                    nature_of_discount = ''
                    nature_of_discount = 'porcentaje'
                    LineaDetalle += '[NaturalezaDescuento]' + str(nature_of_discount) + '[|NaturalezaDescuento]'
                LineaDetalle += '[SubTotal]' + str('%023.5f' % line.price_subtotal) + '[|SubTotal]'
                if line.invoice_line_tax_ids:
                    LineaDetalle += '[Impuesto]'

                    for tax_ids in line.invoice_line_tax_ids:
                        LineaDetalle += '[Codigo]' + tax_ids.tax_code + '[|Codigo]'
                        LineaDetalle += '[Tarifa]' + str(format(round_curr(tax_ids.amount), '.5f')) + '[|Tarifa]'
                        product_amount = line.quantity * line.price_unit
                        product_amount_after_discount = product_amount - (
                            product_amount * (line.discount / 100))
                        LineaDetalle += '[Monto]' + str(
                            '%023.5f' % round_curr(product_amount_after_discount * (tax_ids.amount / 100))) + '[|Monto]'

                        if tax_ids.tax_code in ('08', '09', '10', '11', '99'):
                            LineaDetalle += '[Exoneracion]'
                            LineaDetalle += '[TipoDocumento]' + str(tax_ids.tax_exemption_code) + '[|TipoDocumento]'
                            LineaDetalle += '[NumeroDocumento]' + str(
                                tax_ids.tax_exemption_number) + '[|NumeroDocumento]'
                            LineaDetalle += '[NombreInstitucion]' + str(
                                tax_ids.tax_exemption_issuer_number) + '[|NombreInstitucion]'
                            LineaDetalle += '[FechaEmision]' + str(
                                self.get_costa_date_time(tax_ids.tax_exemption_date_time)) + '[|FechaEmision]'
                            LineaDetalle += '[MontoImpuesto]' + str(tax_ids.tax_authorized_amount) + '[|MontoImpuesto]'
                            LineaDetalle += '[PorcentajeCompra]' + str(
                                tax_ids.tax_authorized_percentage) + '[|PorcentajeCompra]'
                            LineaDetalle += '[|Exoneracion]'

                    LineaDetalle += '[|Impuesto]'

                LineaDetalle += '[MontoTotalLinea]' + str('%023.5f' % line.price_total) + '[|MontoTotalLinea]'
                LineaDetalle += '[|LineaDetalle]'
            DetalleServicio = LineaDetalle
            invoice_dict += '[DetalleServicio]' + DetalleServicio + '[|DetalleServicio]'

            ResumenFactura = ''

            total_service_exempt = 0.0
            total_sub_total = 0.0
            total_goods_exempt = 0.0
            diff = 0.0
            for line in id.invoice_line_ids:
                diff = line.price_total - line.price_subtotal
                if line.product_id.type == 'service':
                    if diff == 0.0:
                        total_service_exempt += line.price_total
                total_sub_total += line.quantity * line.price_unit

            for line in id.invoice_line_ids:
                diff = line.price_total - line.price_subtotal
                if line.product_id.type != 'service':
                    if diff == 0.0:
                        total_goods_exempt += line.price_total

            TotalServGravados = 0.0
            TotalGravado = 0.0
            TotalMercanciasGravadas = 0.0
            TotalImpuesto = 0.0
            TotalVentaNeta = 0.0
            TotalMercanciasExentas = total_goods_exempt
            for tax_line in id.tax_line_ids:
                if tax_line.tax_id.tax_code == '07':
                    if tax_line.amount_total > 0:
                        TotalServGravados += tax_line.base
                        TotalGravado += tax_line.base
                        TotalImpuesto += tax_line.amount_total
                if tax_line.tax_id.tax_code in ('01', '02', '03', '04', '05', '06', '12', '98'):
                    if tax_line.amount_total > 0:
                        TotalMercanciasGravadas += tax_line.base
                        TotalGravado += tax_line.base
                        TotalImpuesto += tax_line.amount_total
            TotalGravado = TotalServGravados + TotalMercanciasGravadas
            TotalServExentos = total_service_exempt

            TotalExento = TotalServExentos + TotalMercanciasExentas
            # TotalVenta = total_sub_total
            TotalVenta = TotalGravado + TotalExento
            TotalVentaNeta = TotalVenta - TotalDescuentos
            ResumenFactura = '[ResumenFactura][CodigoMoneda]' + id.currency_id.name + '[|CodigoMoneda]'
            ResumenFactura += '[TipoCambio]' + str('%023.5f' % id.currency_id.rate) + '[|TipoCambio]'
            ResumenFactura += '[TotalServGravados]' + str('%023.5f' % TotalServGravados) + '[|TotalServGravados]'
            ResumenFactura += '[TotalServExentos]' + str('%023.5f' % TotalServExentos) + '[|TotalServExentos]'
            ResumenFactura += '[TotalMercanciasGravadas]' + str(
                '%023.5f' % TotalMercanciasGravadas) + '[|TotalMercanciasGravadas]'
            ResumenFactura += '[TotalMercanciasExentas]' + str(
                '%023.5f' % TotalMercanciasExentas) + '[|TotalMercanciasExentas]'
            ResumenFactura += '[TotalGravado]' + str('%023.5f' % TotalGravado) + '[|TotalGravado]'
            ResumenFactura += '[TotalExento]' + str('%023.5f' % TotalExento) + '[|TotalExento]'
            ResumenFactura += '[TotalVenta]' + str('%023.5f' % TotalVenta) + '[|TotalVenta]'
            ResumenFactura += '[TotalDescuentos]' + str('%023.5f' % TotalDescuentos) + '[|TotalDescuentos]'
            ResumenFactura += '[TotalVentaNeta]' + str('%023.5f' % (TotalVentaNeta )) + '[|TotalVentaNeta]'
            ResumenFactura += '[TotalImpuesto]' + str('%023.5f' % TotalImpuesto) + '[|TotalImpuesto]'
            ResumenFactura += '[TotalComprobante]' + str('%023.5f' % (TotalVentaNeta + TotalImpuesto )) + '[|TotalComprobante]'
            ResumenFactura += '[|ResumenFactura]'

            invoice_dict += ResumenFactura

            InformacionReferencia = '[InformacionReferencia]'
            InformacionReferencia +=    '[TipoDoc]'+ type + '[|TipoDoc]'
            InformacionReferencia +=    '[Numero]'+ Clave+'[|Numero]'
            InformacionReferencia +=    '[FechaEmision]'+ FechaEmision+'[|FechaEmision]'
            InformacionReferencia +=    '[Codigo]'+ '05'+'[|Codigo]'
            InformacionReferencia +=    '[Razon]'+ Clave+'[|Razon]'
            InformacionReferencia += '[|InformacionReferencia]'

            invoice_dict += InformacionReferencia

            Normativa = None

            if type == '01':
                Normativa = '[Normativa][NumeroResolucion]DGT-R-48-2016[|NumeroResolucion][FechaResolucion]07-10-2016 08:00:00[|FechaResolucion][|Normativa]'
            elif type == '02':
                Normativa = '[Normativa][NumeroResolucion]DGT-R-48-2016[|NumeroResolucion][FechaResolucion]07-10-2016 08:00:00[|FechaResolucion][|Normativa]'
            elif type == '03':
                Normativa = '[Normativa][NumeroResolucion]DGT-R-48-2016[|NumeroResolucion][FechaResolucion]07-10-2016 08:00:00[|FechaResolucion][|Normativa]'


            invoice_dict += Normativa
            invoice_dict += '[|root]'

            id.clave_numerica = Clave

            try:
                res = requests.post(id.company_id.url + '/api/hacienda', {
                    'data': base64.b64encode(invoice_dict.encode()),
                    'key': id.company_id.access_token,
                    'clave': Clave,
                    'date': str(id.date_invoice),
                    'fecha': FechaEmision,
                    'type': type,
                    'vat': id.company_id.company_registry,
                    'emisor': json.dumps({
                        'tipoIdentificacion': id.company_id.partner_id.tipo,
                        'numeroIdentificacion': id.company_id.company_registry
                    }),
                    'receptor': json.dumps({
                        'tipoIdentificacion': id.partner_id.tipo,
                        'numeroIdentificacion': id.partner_id.vat
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
                    try:
                        return id.invoice_print()
                    except:
                        pass

                except:
                    id.response = res


            except requests.exceptions.RequestException:
                if not cron:
                    raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
                else:
                    pass
            except requests.exceptions.HTTPError:
                if not cron:
                    raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
                else:
                    pass
            except requests.exceptions.ConnectionError:
                if not cron:
                    raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
                else:
                    pass
            except requests.exceptions.Timeout:
                if not cron:
                    raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
                else:
                    pass


    @api.onchange('xml_supplier_approval')
    def _onchange_xml_supplier_approval(self):
        if self.xml_supplier_approval:
            root = ET.fromstring(re.sub(' xmlns="[^"]+"', '', base64.b64decode(self.xml_supplier_approval).decode(), count=1))#quita el namespace de los elementos
            if not root.findall('Clave'):
                return {'value': {'xml_supplier_approval': False},'warning': {'title': 'Atención','message': 'El archivo xml no contiene el nodo Clave. Por favor cargue un archivo con el formato correcto.'}}
            if not root.findall('FechaEmision'):
                return {'value': {'xml_supplier_approval': False},'warning': {'title': 'Atención','message': 'El archivo xml no contiene el nodo FechaEmision. Por favor cargue un archivo con el formato correcto.'}}
            if not root.findall('Emisor'):
                return {'value': {'xml_supplier_approval': False},'warning': {'title': 'Atención','message': 'El archivo xml no contiene el nodo Emisor. Por favor cargue un archivo con el formato correcto.'}}
            if not root.findall('Emisor')[0].findall('Identificacion'):
                return {'value': {'xml_supplier_approval': False},'warning': {'title': 'Atención','message': 'El archivo xml no contiene el nodo Identificacion. Por favor cargue un archivo con el formato correcto.'}}
            if not root.findall('Emisor')[0].findall('Identificacion')[0].findall('Tipo'):
                return {'value': {'xml_supplier_approval': False},'warning': {'title': 'Atención','message': 'El archivo xml no contiene el nodo Tipo. Por favor cargue un archivo con el formato correcto.'}}
            if not root.findall('Emisor')[0].findall('Identificacion')[0].findall('Numero'):
                return {'value': {'xml_supplier_approval': False},'warning': {'title': 'Atención','message': 'El archivo xml no contiene el nodo Numero. Por favor cargue un archivo con el formato correcto.'}}
            if not (root.findall('ResumenFactura') and root.findall('ResumenFactura')[0].findall('TotalImpuesto')):
                return {'value': {'xml_supplier_approval': False},'warning': {'title': 'Atención','message': 'No se puede localizar el nodo TotalImpuesto. Por favor cargue un archivo con el formato correcto.'}}
            if not (root.findall('ResumenFactura') and root.findall('ResumenFactura')[0].findall('TotalComprobante')):
                return {'value': {'xml_supplier_approval': False},'warning': {'title': 'Atención','message': 'No se puede localizar el nodo TotalComprobante. Por favor cargue un archivo con el formato correcto.'}}

    @api.multi
    def charge_xml_data(self):
        if self.xml_supplier_approval:
            root = ET.fromstring(re.sub(' xmlns="[^"]+"', '', base64.b64decode(self.xml_supplier_approval).decode(), count=1))#quita el namespace de los elementos
            self.clave_numerica = root.findall('Clave')[0].text
            self.date = root.findall('FechaEmision')[0].text
            partner = self.env['res.partner'].search([('vat', '=', root.findall('Emisor')[0].find('Identificacion')[1].text)])
            if partner:
                self.partner_id = partner.id
            else:
                raise UserError('El proveedor con identificación '+root.findall('Emisor')[0].find('Identificacion')[1].text+' no existe. Por favor creelo primero en el sistema.')


    @api.multi
    def send_xml(self):
        invoice_dict = ''
        for id in self:
            if id.xml_supplier_approval:
                root = ET.fromstring(re.sub(' xmlns="[^"]+"', '', base64.b64decode(id.xml_supplier_approval).decode(), count=1))
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
                        NumeroConsecutivo = str(id.company_id.store_branch) + id.terminal.name + type + str(id.number)

                        invoice_dict += '[NumeroCedulaEmisor]' + str(root.findall('Emisor')[0].findall('Identificacion')[0].findall('Numero')[0].text).zfill(12)  + '[|NumeroCedulaEmisor]'
                        invoice_dict += '[FechaEmisionDoc]' + root.findall('FechaEmision')[0].text + '[|FechaEmisionDoc]'
                        invoice_dict += '[Mensaje]' +  id.state_invoice_partner + '[|Mensaje]'
                        invoice_dict += '[DetalleMensaje]' +  detalle_mensaje + '[|DetalleMensaje]'
                        invoice_dict += '[MontoTotalImpuesto]' +  root.findall('ResumenFactura')[0].findall('TotalImpuesto')[0].text + '[|MontoTotalImpuesto]'
                        invoice_dict += '[TotalFactura]' +  root.findall('ResumenFactura')[0].findall('TotalComprobante')[0].text + '[|TotalFactura]'
                        invoice_dict += '[NumeroCedulaReceptor]' +  str(root.findall('Receptor')[0].findall('Identificacion')[0].findall('Numero')[0].text).zfill(12) + '[|NumeroCedulaReceptor]'
                        invoice_dict += '[NumeroConsecutivoReceptor]' +   NumeroConsecutivo + '[|NumeroConsecutivoReceptor]'

            invoice_dict += '[|root]'


            try:
                url = id.company_id.url + '/api/hacienda'

                res = requests.post(url, {
                    'data': base64.b64encode(invoice_dict.encode()),
                    'key': id.company_id.access_token,
                    'clave': root.findall('Clave')[0].text,
                    'fecha': root.findall('FechaEmision')[0].text,
                    'type': type,
                    'date': str(id.date_invoice),
                    'vat': id.company_id.company_registry,
                    'emisor': json.dumps({
                        'tipoIdentificacion': root.findall('Emisor')[0].findall('Identificacion')[0].findall('Numero')[0].text ,
                        'numeroIdentificacion':root.findall('Emisor')[0].findall('Nombre')[0].text
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


    def _get_phone(self, id):
        if id.phone:
            return str(id.phone)
        return ''

    def _get_fax(self, id):
        if id.fax_no:
            return str(id.fax_no)
        return ''

    def _get_name(self, name, empty_space=False):
        if name:
            return self._get_string(name.name, empty_space)

        return ''

    def _get_code(self, code):
        if code:
            return code.code

        return ''

    def _get_string(self, string, empty_space=False):
        if string and string != False:
            if empty_space and len(string) > 0:
                string = string + ''
            return string
        return ''

    def _get_full_address(self, object):
        address = ''
        address += self._get_string(object.street, True) + self._get_string(object.street2, True) + self._get_name(
            object.locality_id, True) + self._get_name(object.district_id, True) + self._get_name(object.canton_id,
                                                                                                  True) + self._get_name(
            object.province_id, True) + self._get_name(object.country_id, True) + self._get_string(object.zip, True)
        return address[0:160]

    def _get_issuer_name(self, id):
        if self._get_doc_type(id) and self._get_doc_type(id).name:
            return self._get_doc_type(id).name
        else:
            raise UserError(_('Los datos requeridos faltan o están vacíosLos datos requeridos faltan o están vacíos'))

    def _get_vat_no(self, id):
        if self._get_doc_type(id).vat and len(self._get_doc_type(id).vat) <= 12 and len(
                self._get_doc_type(id).vat) > 0 and self._no_special(
            self._get_doc_type(id).vat):
            return self._get_doc_type(id).vat
        else:
            raise UserError(_('Los datos requeridos faltan o están vacíosLos datos requeridos faltan o están vacíos'))

    def _get_company_registry_no(self, id):
        if self._get_doc_type(id).company_registry and len(
                self._get_doc_type(id).company_registry) <= 12 and len(
            self._get_doc_type(id).company_registry) > 0 and self._no_special(
            self._get_doc_type(id).company_registry):
            return self._get_doc_type(id).company_registry
        else:
            raise UserError(_('Los datos requeridos faltan o están vacíosLos datos requeridos faltan o están vacíos'))

    def _no_special(self, character):
        all_normal_characters = string.ascii_letters + string.digits
        for char in character:
            if char not in all_normal_characters:
                return False
        return True

    def _is_number(self, data, field):
        if len(data) > 20:
            raise UserError(_(
                'Los datos requeridos faltan o están vacíosSolo un máximo de 20 caracteres permitidos para el campo - ' + field.field_description))
        if data.isdigit():
            return data

        raise UserError(_(
            'Los datos requeridos faltan o están vacíosSolo números permitidos para el campo - ' + field.field_description))

    def _company_registry_no(self, data, field):
        if data.company_registry and len(data.company_registry) <= 12 and self._no_special(data.company_registry):
            return data.company_registry

        raise UserError(_(
            'Verifique su número de registro de la empresa no puede tener más de 12 caracteres y no se permiten caracteres especiales'))

    def _vat(self, data, field):
        if len(data.vat) > 13:
            raise UserError(_(
                'Los datos requeridos faltan o están vacíosSolo un máximo de 13 caracteres permitidos para el campo - ' + field.field_description))
        return data.vat

    def _full_address(self, data, field):
        address = ''
        address += self._get_string(data.street, True) + self._get_string(data.street2, True) + self._get_name(
            data.locality_id, True) + self._get_name(data.district_id, True) + self._get_name(data.canton_id,
                                                                                              True) + self._get_name(
            data.province_id, True) + self._get_name(data.country_id, True) + self._get_string(data.zip, True)
        return address[0:160]

    def _version(self, data, field):
        return '4.5'

    def _invoice_time(self, data, field):
        return '00:00:00'

    def _check_required(self, data, description):
        if data != False:
            return True

        raise UserError(
            _('Los datos requeridos faltan o están vacíosRequired data is missing for the field - ' + description))

    def _state(self, id):
        if id.type == 'out_refund':
            return '0'
        return '1'

    def _doc_type(self, id):
        if id.type == 'out_invoice':
            return '01'
        elif id.type == 'out_refund':
            return '02'
        elif id.type == 'in_refund':
            return '03'

    def _get_doc_type(self, id, opp=False):
        if opp:
            return id.partner_id
        return id.company_id

    def get_costa_date_time(self, value, format='%Y-%m-%d %H:%M:%S'):
        if type(value) == str:
            value = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        date_time = datetime.datetime.strptime(value.strftime(format), format) - datetime.timedelta(hours=6)
        return date_time.strftime(format)

    def get_costa_date_time_with_t(self, value, format='%Y-%m-%dT%H:%M:%S'):
        if type(value) == str:
            value = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
        date_time = datetime.datetime.strptime(value.strftime(format), format) - datetime.timedelta(hours=6)
        return date_time.strftime(format) + '-06:00'

    def get_costa_date_time_with_t_2(self, value, format='%Y-%m-%dT%H:%M:%S.%f'):
        if type(value) == str:
            value = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
        date_time = datetime.datetime.strptime(value.strftime(format), format) - datetime.timedelta(hours=6)
        return date_time.strftime(format) + '-06:00'



    state_invoice_partner = fields.Selection([('1', 'Aceptado'), ('3', 'Rechazado'), ('2', 'Aceptacion parcial')], 'Respuesta del Cliente')
    xml_supplier_approval = fields.Binary(string="XML Proveedor", required=False, copy=False, attachment=True)

