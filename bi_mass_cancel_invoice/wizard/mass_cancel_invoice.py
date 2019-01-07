# -*- coding: utf-8 -*-

from odoo import models,fields,api
from odoo.exceptions import UserError, AccessError

class MassCancelTransfer(models.Model):
	_name = 'mass.cancel.wizard.invoice'

	mass_cancel_invoice= fields.Boolean(required=True)

	@api.multi
	def on_click_invoice(self):
		invoice_quot=self.env["account.invoice"].browse(self._context.get('active_ids',[]))

		for invoices in invoice_quot:
			if not invoices.journal_id.update_posted and invoices.state=="open":
				raise UserError(("You cannot modify a posted entry of this journal.\nFirst you should set the journal to allow cancelling entries."))

		if self.mass_cancel_invoice == False:
			raise UserError(('Please give permission by clicking the check-box to cancel selected invoices.'))

		if self.mass_cancel_invoice == True:
			if any(invoice.state=='paid' for invoice in invoice_quot):
				invoice_list=[]
				for invoice in invoice_quot:
					if invoice.state=='paid':
						invoice_list.append(invoice.number)
						invoice_str = str(invoice_list).strip('[]')

				raise UserError(('You Cannot cancel paid invoice..! \n Your paid invoice is/are:{}'.format(invoice_str)))
			
			if any(invoice.state!='paid' for invoice in invoice_quot):
				invoice_quot.write({'state':'cancel'})

