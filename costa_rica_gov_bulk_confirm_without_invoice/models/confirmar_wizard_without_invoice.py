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


class ConfirmarWithoutInvoiceWizard(models.Model):
    _name = 'confirmar.wizard.without.invoice'
    _rec_name = 'terminal'

    state_invoice_partner = fields.Selection([('1', 'Aceptado'), ('3', 'Rechazado'), ('2', 'Aceptacion parcial')],
                                            'Respuesta del Cliente', required=True)
    terminal = fields.Many2one('terminal', required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id, required=True)
    comfirmar_ids = fields.One2many('confirmar.without.invoice','wizard_id')

    @api.multi
    def action_bulk_confirm_xml(self):
        for id in self.comfirmar_ids:
            id.terminal = self.terminal.id
            id.company_id = self.company_id.id
            id.state_invoice_partner = self.state_invoice_partner
            id.wizard_id = self.id
            id.charge_xml_data()
            id.send_xml()

        return {
            'name': _('Bulk Confirmar'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'confirmar.without.invoice',
            'type': 'ir.actions.act_window',
        }