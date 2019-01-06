# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, _
from odoo.exceptions import UserError


class CancelAccountMove(models.TransientModel):
    _name = "cancel.account.move"
    _description = "Cancel Account Move"


    @api.multi
    def cancel_move(self):
        context = dict(self._context or {})
        moves = self.env['account.move'].browse(context.get('active_ids'))
        for move in moves:
            if not move.journal_id.update_posted:
                raise UserError(_('You cannot modify a posted entry of this journal.\nFirst you should set the journal to allow cancelling entries.'))
        if moves.ids:
            moves._check_lock_date()
            moves._cr.execute('UPDATE account_move '\
                       'SET state=%s '\
                       'WHERE id IN %s', ('draft', tuple(moves.ids),))
            self.invalidate_cache()
        moves._check_lock_date()
        return True