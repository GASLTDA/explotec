from odoo import models, fields, api,_
from odoo.exceptions import UserError

class ConfimarWizard(models.TransientModel):
    _name = 'confimar.wizard'
    _rec_name = 'terminal'

    @api.multi
    def get_selected(self):
        if self.env.context.get('active_ids', False):
            for id in self.env.context.get('active_ids'):
                id = self.env['account.invoice'].browse(id)

                if id.type != 'in_invoice':
                    raise UserError(_('Por favor seleccione la factura del proveedor'))
                if  id.state == 'draft':
                    raise UserError(_('Por favor, valide la factura antes de confirmar xml'))

                if id.haicenda_status == 'aceptado' or id.haicenda_status == 'procesando':
                    raise UserError(_(id.number+ ' - ' + 'ya enviado'))

            return self.env.context.get('active_ids')
        else:
            raise UserError(_('Ninguna factura seleccionada'))

    name = fields.Many2many('account.invoice',string='Invoice', required=True, default=lambda self: self.get_selected())
    state_invoice_partner = fields.Selection([('1', 'Aceptado'), ('3', 'Rechazado'), ('2', 'Aceptacion parcial')], 'Respuesta del Cliente')
    terminal = fields.Many2one('terminal')


    @api.multi
    def action_bulk_confirm_xml(self):
        for id in self.name:
            if id.xml_supplier_approval:
                id.state_invoice_partner = self.state_invoice_partner
                id.terminal = self.terminal
                id.charge_xml_data()
                id.send_xml()