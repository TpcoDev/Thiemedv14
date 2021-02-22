# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class DTECompany(models.Model):
    _inherit = 'res.company'


    def _get_default_tp_type(self):
        try:
            return self.env.ref('l10n_cl_fe.res_IVARI')
        except:
            return self.env['sii.responsability']

    def _get_default_doc_type(self):
        try:
            return self.env.ref('l10n_cl_fe.dt_RUT')
        except:
            return self.env['sii.document_type']

    dte_email = fields.Char(
            'DTE Email')
            
    dte_service_provider = fields.Selection(
            (
                ('SIICERT', 'SII - Certification process'),
                ('SII', 'www.sii.cl'),
            ),
            string='DTE Service Provider',
            help='''Please select your company service \
provider for DTE service.
    ''',
            default='SIICERT',
        )
    dte_resolution_number = fields.Char(
            string='SII Exempt Resolution Number',
    )
    dte_resolution_date = fields.Date(
            'SII Exempt Resolution Date',
    )
    sii_regional_office_id = fields.Char(
            string='SII Regional Office',
        )
    state_id = fields.Many2one(
            string='Ubication',
        )
    company_activities_ids = fields.Char(

            string='Activities Names',
        )
    responsability_id = fields.Char(
            string="Responsability"
        )
    start_date = fields.Char(
            string='Start-up Date'
        )
    invoice_vat_discrimination_default = fields.Selection(
            [
                    ('no_discriminate_default', 'Yes, No Discriminate Default'),
                    ('discriminate_default', 'Yes, Discriminate Default')
            ],
            string='Invoice VAT discrimination default',
            default='no_discriminate_default',
            required=True,
            help="""Define behaviour on invoices reports. Discrimination or not \
 will depend in partner and company responsability and SII letters\
        setup:
            * If No Discriminate Default, if no match found it won't \
            discriminate by default.
            * If Discriminate Default, if no match found it would \
            discriminate by default.
            """
        )
    activity_description = fields.Char(
            string='Glosa Giro',
        )
    city_id = fields.Char(
            string='City',
        )
    document_number = fields.Char('docnumber'
        )
    document_type_id = fields.Char(
            string='Document type',
        )


# class AccountPaymentGroup(models.Model):
#     _name = "account.payment.group"
#     _description = "Payment Group"
#     _order = "payment_date desc"
#     _inherit = 'mail.thread'

#     company_id = fields.Char(
#         string='Company',
#         required=True,
#         index=True,
#         default=lambda self: self.env.user.company_id,
#         readonly=True,
#         states={'draft': [('readonly', False)]},
#     )
#     payment_methods = fields.Char(
#         string='Métodos de pago',
#         compute='_compute_payment_methods',
#         search='_search_payment_methods',
#     )
#     partner_type = fields.Selection(
#         [('customer', 'Customer'), ('supplier', 'Vendor')],
#         track_visibility='always',
#     )
#     partner_id = fields.Char(
#         string='Partner',
#         required=True,
#         readonly=True,
#         states={'draft': [('readonly', False)]},
#         track_visibility='always',
#     )
#     commercial_partner_id = fields.Char(
#         readonly=True,
#     )
#     currency_id = fields.Char(
#         string='Currency',
#         required=True,
#         default=lambda self: self.env.user.company_id.currency_id,
#         readonly=True,
#         states={'draft': [('readonly', False)]},
#         track_visibility='always',
#     )
#     payment_date = fields.Date(
#         string='Payment Date',
#         default=fields.Date.context_today,
#         required=True,
#         copy=False,
#         readonly=True,
#         states={'draft': [('readonly', False)]},
#     )
#     communication = fields.Char(
#         string='Memo',
#         readonly=True,
#         states={'draft': [('readonly', False)]},
#     )
#     notes = fields.Text(
#         string='Notes'
#     )
#     matched_amount = fields.Monetary(
#         currency_field='currency_id',
#     )
#     unmatched_amount = fields.Monetary(
#         compute='_compute_matched_amounts',
#         currency_field='currency_id',
#     )
#     selected_finacial_debt = fields.Monetary(
#         string='Selected Financial Debt',
#         compute='_compute_selected_debt',
#     )
#     selected_debt = fields.Monetary(
#         # string='To Pay lines Amount',
#         string='Selected Debt',
#         compute='_compute_selected_debt',
#     )
#     # this field is to be used by others
#     selected_debt_untaxed = fields.Monetary(
#         # string='To Pay lines Amount',
#         string='Selected Debt Untaxed',
#         compute='_compute_selected_debt',
#     )
#     unreconciled_amount = fields.Monetary(
#         string='Adjusment / Advance',
#         readonly=True,
#         states={'draft': [('readonly', False)]},
#     )
#     # reconciled_amount = fields.Monetary(compute='_compute_amounts')
#     to_pay_amount = fields.Monetary(
#         string='To Pay Amount',
#         # string='Total To Pay Amount',
#         readonly=True,
#         states={'draft': [('readonly', False)]},
#         track_visibility='always',
#     )

#     payments_amount = fields.Monetary(
#         string='Amount',
#         track_visibility='always',
#     )
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('confirmed', 'Confirmed'),
#         ('posted', 'Posted'),
#         # ('sent', 'Sent'),
#         # ('reconciled', 'Reconciled')
#         ('cancel', 'Cancelled'),
#     ], readonly=True, default='draft', copy=False, string="Status",
#         track_visibility='onchange',
#     )
#     move_lines_domain = (
#         "["
#         "('partner_id.commercial_partner_id', '=', commercial_partner_id),"
#         "('account_id.internal_type', '=', account_internal_type),"
#         "('account_id.reconcile', '=', True),"
#         "('reconciled', '=', False),"
#         "('company_id', '=', company_id),"
#         # '|',
#         # ('amount_residual', '!=', False),
#         # ('amount_residual_currency', '!=', False),
#         "]")
#     debt_move_line_ids = fields.Char(
#         string="Debt Lines",
#         readonly=True,
#         states={'draft': [('readonly', False)]},
#     )
#     has_outstanding = fields.Boolean(
#         compute='_compute_has_outstanding',
#     )
#     to_pay_move_line_ids = fields.Char(
#         string="To Pay Lines",
#         help='This lines are the ones the user has selected to be paid.',
#         copy=False)
#     matched_move_line_ids = fields.Char(
#         help='Lines that has been matched to payments, only available after '
#         'payment validation',
#     )
#     payment_subtype = fields.Char(
#         compute='_compute_payment_subtype'
#     )
#     pop_up = fields.Boolean(
#         # campo que agregamos porque el  invisible="context.get('pop_up')"
#         # en las pages no se comportaba bien con los attrs
#         compute='_compute_payment_pop_up',
#         default=lambda x: x._context.get('pop_up', False),
#     )

#     payment_difference = fields.Monetary(
#         compute='_compute_payment_difference',
#         # TODO rename field or remove string
#         # string='Remaining Residual',
#         readonly=True,
#         string="Payments Difference",
#         help="Difference between selected debt (or to pay amount) and "
#         "payments amount"
#     )
#     payment_ids = fields.Char(
#         string='Payment Lines',
#         ondelete='cascade',
#     )
#     move_line_ids = fields.Char(
#         readonly=True,
#         copy=False,
#     )
#     account_internal_type = fields.Char(string='catha'
#     )

#     @api.model
#     def create(self, vals):
#         if 'payment_ids' not in vals:
#             raise ValidationError('No debe registrar un pago sin líneas de pago')
#         vals.update({'debt_move_line_ids': vals['to_pay_move_line_ids']})
#         return super(AccountPaymentGroup, self).create(vals)

#     # @api.multi
#     def onchange(self, values, field_name, field_onchange):
#         """
#         En este caso es distinto el fix al uso que le damos para domains [0][2]
#         de campos x2many en vista. En este caso lo necesitamos porque la mejora
#         que hicieron de vistas de alguna menra molesta y hace pensar que
#         estamos escribiendo los move lines, con esto se soluciona
#         """
#         #for field in list(field_onchange):
#         #    if field.startswith((
#         #            'to_pay_move_line_ids.',
#         #            'debt_move_line_ids.')):
#         #        del field_onchange[field]
#         return super(AccountPaymentGroup, self).onchange(
#             values, field_name, field_onchange)


#     # @api.multi
#     @api.depends(
#         'state',
#         'payments_amount',
#         'matched_move_line_ids.payment_group_matched_amount')
#     def _compute_matched_amounts(self):
#         for rec in self:
#             if rec.state != 'posted':
#                 continue
#             # damos vuelta signo porque el payments_amount tmb lo da vuelta,
#             # en realidad porque siempre es positivo y se define en funcion
#             # a si es pago entrante o saliente
#             sign = rec.partner_type == 'supplier' and -1.0 or 1.0
#             rec.matched_amount = sign * sum(
#                 rec.matched_move_line_ids.with_context(
#                     payment_group_id=rec.id).mapped(
#                         'payment_group_matched_amount'))
#             rec.unmatched_amount = rec.payments_amount - rec.matched_amount

#     # @api.multi
#     @api.depends('to_pay_move_line_ids')
#     def _compute_has_outstanding(self):
#         for rec in self:
#             if rec.state != 'draft':
#                 continue
#             if rec.partner_type == 'supplier':
#                 # field = 'debit'
#                 lines = rec.to_pay_move_line_ids.filtered(
#                     lambda x: x.amount_residual > 0.0)
#             else:
#                 lines = rec.to_pay_move_line_ids.filtered(
#                     lambda x: x.amount_residual < 0.0)
#             if len(lines) != 0:
#                 rec.has_outstanding = True

#     def _search_payment_methods(self, operator, value):
#         return [('payment_ids.journal_id.name', operator, value)]

#     # @api.multi
#     def _compute_payment_methods(self):
#         # TODO tal vez sea interesante sumar al string el metodo en si mismo
#         # (manual, cheque, etc)

#         # tuvmos que hacerlo asi sudo porque si no tenemos error, si agregamos
#         # el sudo al self o al rec no se computa el valor, probamos tmb
#         # haciendo compute sudo y no anduvo, la unica otra alternativa que
#         # funciono es el search de arriba (pero que no muestra todos los
#         # names)
#         for rec in self:
#             # journals = rec.env['account.journal'].search(
#             #     [('id', 'in', rec.payment_ids.ids)])
#             # rec.payment_methods = ", ".join(journals.mapped('name'))
#             rec.payment_methods = ", ".join(rec.payment_ids.sudo().mapped(
#                 'journal_id.name'))

#     # @api.multi
#     def action_payment_sent(self):
#         raise ValidationError(_('Not implemented yet'))

#     # @api.multi
#     def payment_print(self):
#         raise ValidationError(_('Not implemented yet'))

#     # @api.multi
#     @api.depends('to_pay_move_line_ids')
#     def _compute_debt_move_line_ids(self):
#         for rec in self:
#             rec.debt_move_line_ids = rec.to_pay_move_line_ids

#     # @api.multi
#     @api.onchange('debt_move_line_ids')
#     def _inverse_debt_move_line_ids(self):
#         for rec in self:
#             rec.to_pay_move_line_ids = rec.debt_move_line_ids

#     # @api.multi
#     def _compute_payment_pop_up(self):
#         pop_up = self._context.get('pop_up', False)
#         for rec in self:
#             rec.pop_up = pop_up

#     # @api.multi
#     @api.depends('company_id.double_validation', 'partner_type')
#     def _compute_payment_subtype(self):
#         for rec in self:
#             if (rec.partner_type == 'supplier' and
#                     rec.company_id.double_validation):
#                 payment_subtype = 'double_validation'
#             else:
#                 payment_subtype = 'simple'
#             rec.payment_subtype = payment_subtype

#     # @api.multi
#     def _compute_matched_move_line_ids(self):
#         """
#         Lar partial reconcile vinculan dos apuntes con credit_move_id y
#         debit_move_id.
#         Buscamos primeros todas las que tienen en credit_move_id algun apunte
#         de los que se genero con un pago, etnonces la contrapartida
#         (debit_move_id), son cosas que se pagaron con este pago. Repetimos
#         al revz (debit_move_id vs credit_move_id)
#         """
#         for rec in self:
#             lines = rec.move_line_ids.browse()
#             # not sure why but self.move_line_ids dont work the same way
#             payment_lines = rec.payment_ids.mapped('move_line_ids')

#             reconciles = rec.env['account.partial.reconcile'].search([
#                 ('credit_move_id', 'in', payment_lines.ids)])
#             lines |= reconciles.mapped('debit_move_id')

#             reconciles = rec.env['account.partial.reconcile'].search([
#                 ('debit_move_id', 'in', payment_lines.ids)])
#             lines |= reconciles.mapped('credit_move_id')

#             rec.matched_move_line_ids = lines - payment_lines

#     # @api.multi
#     @api.depends('partner_type')
#     def _compute_account_internal_type(self):
#         for rec in self:
#             if rec.partner_type:
#                 rec.account_internal_type = MAP_PARTNER_TYPE_ACCOUNT_TYPE[
#                     rec.partner_type]

#     # @api.multi
#     @api.depends('to_pay_amount', 'payments_amount')
#     def _compute_payment_difference(self):
#         for rec in self:
#             # if rec.payment_subtype != 'double_validation':
#             #     continue
#             rec.payment_difference = rec.to_pay_amount - rec.payments_amount

#     # @api.multi
#     @api.depends('payment_ids.amount_company_currency')
#     def _compute_payments_amount(self):
#         for rec in self:
#             rec.payments_amount = sum(rec.payment_ids.mapped(
#                 'amount_company_currency'))
#             # payments_amount = sum([
#             #     x.payment_type == 'inbound' and
#             #     x.amount_company_currency or -x.amount_company_currency for
#             #     x in rec.payment_ids])
#             # rec.payments_amount = (
#             #     rec.partner_type == 'supplier' and
#             #     -payments_amount or payments_amount)

#     # TODO analizar en v10
#     # el onchange no funciona bien en o2m, si usamos write se escribe pero no
#     # se actualiza en interfaz lo cual puede ser confuzo, por ahora lo
#     # comentamos
#     # @api.onchange('payment_date')
#     # def change_payment_date(self):
#     #     # self.payment_ids.write({'payment_date': self.payment_date})
#     #     for line in self.payment_ids:
#     #         line.payment_date = self.payment_date

#     # @api.multi
#     @api.depends(
#         'to_pay_move_line_ids.amount_residual',
#         'to_pay_move_line_ids.amount_residual_currency',
#         'to_pay_move_line_ids.currency_id',
#         'to_pay_move_line_ids.invoice_id',
#         'payment_date',
#         'currency_id',
#     )
#     def _compute_selected_debt(self):
#         for rec in self:
#             selected_finacial_debt = 0.0
#             selected_debt = 0.0
#             selected_debt_untaxed = 0.0
#             for line in rec.to_pay_move_line_ids:
#                 selected_finacial_debt += line.financial_amount_residual
#                 selected_debt += line.amount_residual
#                 # factor for total_untaxed
#                 invoice = line.invoice_id
#                 factor = invoice and invoice._get_tax_factor() or 1.0
#                 selected_debt_untaxed += line.amount_residual * factor
#             sign = rec.partner_type == 'supplier' and -1.0 or 1.0
#             rec.selected_finacial_debt = selected_finacial_debt * sign
#             rec.selected_debt = selected_debt * sign
#             rec.selected_debt_untaxed = selected_debt_untaxed * sign

#     # @api.multi
#     @api.depends(
#         'selected_debt', 'unreconciled_amount')
#     def _compute_to_pay_amount(self):
#         for rec in self:
#             rec.to_pay_amount = rec.selected_debt + rec.unreconciled_amount

#     # @api.multi
#     def _inverse_to_pay_amount(self):
#         for rec in self:
#             rec.unreconciled_amount = rec.to_pay_amount - rec.selected_debt

#     # @api.multi
#     @api.onchange('partner_id', 'partner_type', 'company_id')
#     def _refresh_payments_and_move_lines(self):
#         # clean actual invoice and payments
#         # no hace falta
#         if self._context.get('pop_up'):
#             return
#         for rec in self:
#             # not sure why but state field is false on payments so they can
#             # not be unliked, this fix that
#             rec.invalidate_cache(['payment_ids'])

#     # @api.multi
#     def _get_to_pay_move_lines_domain(self):
#         self.ensure_one()
#         return [
#             ('partner_id.commercial_partner_id', '=',
#                 self.commercial_partner_id.id),
#             ('account_id.internal_type', '=',
#                 self.account_internal_type),
#             ('account_id.reconcile', '=', True),
#             ('reconciled', '=', False),
#             ('company_id', '=', self.company_id.id),
#             # '|',
#             # ('amount_residual', '!=', False),
#             # ('amount_residual_currency', '!=', False),
#         ]

#     # @api.multi
#     def add_all(self):
#         for rec in self:
#             rec.to_pay_move_line_ids = rec.env['account.move.line'].search(
#                 rec._get_to_pay_move_lines_domain())

#     # @api.multi
#     def remove_all(self):
#         self.to_pay_move_line_ids = False

#     @api.model
#     def default_get(self, fields):
#         # TODO si usamos los move lines esto no haria falta
#         rec = super(AccountPaymentGroup, self).default_get(fields)
#         to_pay_move_line_ids = self._context.get('to_pay_move_line_ids')
#         to_pay_move_lines = self.env['account.move.line'].browse(
#             to_pay_move_line_ids).filtered(lambda x: (
#                 x.account_id.reconcile and
#                 x.account_id.internal_type in ('receivable', 'payable')))
#         if to_pay_move_lines:
#             partner = to_pay_move_lines.mapped('partner_id')
#             if len(partner) != 1:
#                 raise ValidationError(_(
#                     'You can not send to pay lines from different partners'))

#             internal_type = to_pay_move_lines.mapped(
#                 'account_id.internal_type')
#             if len(internal_type) != 1:
#                 raise ValidationError(_(
#                     'You can not send to pay lines from different partners'))
#             rec['partner_id'] = partner[0].id
#             rec['partner_type'] = MAP_ACCOUNT_TYPE_PARTNER_TYPE[
#                 internal_type[0]]
#             # rec['currency_id'] = invoice['currency_id'][0]
#             # rec['payment_type'] = (
#             #     internal_type[0] == 'receivable' and
#             #     'inbound' or 'outbound')
#             rec['to_pay_move_line_ids'] = [(6, False, to_pay_move_line_ids)]
#         return rec

#     # @api.multi
#     def button_journal_entries(self):
#         return {
#             'name': _('Journal Items'),
#             'view_type': 'form',
#             'view_mode': 'tree,form',
#             'res_model': 'account.move.line',
#             'view_id': False,
#             'type': 'ir.actions.act_window',
#             'domain': [('payment_id', 'in', self.payment_ids.ids)],
#         }

#     # @api.multi
#     def unreconcile(self):
#         for rec in self:
#             rec.payment_ids.unreconcile()
#             # TODO en alguos casos setear sent como en payment?
#             rec.write({'state': 'posted'})

#     # @api.multi
#     def cancel(self):
#         for rec in self:
#             # because child payments dont have invoices we remove reconcile
#             for move in rec.move_line_ids.mapped('move_id'):
#                 rec.matched_move_line_ids.remove_move_reconcile()
#                 # TODO borrar esto si con el de arriba va bien
#                 # if rec.to_pay_move_line_ids:
#                 #     move.line_ids.remove_move_reconcile()
#             rec.payment_ids.cancel()
#             rec.state = 'cancel'

#     # @api.multi
#     def action_draft(self):
#         self.mapped('payment_ids').action_draft()
#         return self.write({'state': 'draft'})

#     # @api.multi
#     def unlink(self):
#         if any(rec.state != 'draft' for rec in self):
#             raise ValidationError(_(
#                 "You can not delete a payment that is already posted"))
#         return super(AccountPaymentGroup, self).unlink()

#     # @api.multi
#     def confirm(self):
#         for rec in self:
#             accounts = rec.to_pay_move_line_ids.mapped('account_id')
#             if len(accounts) > 1:
#                 raise ValidationError(_(
#                     'To Pay Lines must be of the same account!'))
#             rec.state = 'confirmed'

#     # @api.multi
#     def post(self):
#         # dont know yet why, but if we came from an invoice context values
#         # break behaviour, for eg. with demo user error writing account.account
#         # and with other users, error with block date of accounting
#         # TODO we should look for a better way to solve this
#         self = self.with_context({})
#         for rec in self:
#             # TODO if we want to allow writeoff then we can disable this
#             # constrain and send writeoff_journal_id and writeoff_acc_id
#             if not rec.payment_ids:
#                 raise ValidationError(_(
#                     'You can not confirm a payment group without payment '
#                     'lines!'))
#             if (rec.payment_subtype == 'double_validation' and
#                     rec.payment_difference):
#                 raise ValidationError(_(
#                     'To Pay Amount and Payment Amount must be equal!'))

#             writeoff_acc_id = False
#             writeoff_journal_id = False

#             #raise ValidationError(_(
#             #        'No se puede registrar el pago!'))
#             rec.payment_ids.post()
#             counterpart_aml = rec.payment_ids.mapped('move_line_ids').filtered(
#                 lambda r: not r.reconciled and r.account_id.internal_type in (
#                     'payable', 'receivable'))
#             # porque la cuenta podria ser no recivible y ni conciliable
#             # (por ejemplo en sipreco)
#             if counterpart_aml and rec.to_pay_move_line_ids:
#                 (counterpart_aml + (rec.to_pay_move_line_ids)).reconcile(
#                     writeoff_acc_id, writeoff_journal_id)
#             rec.state = 'posted'



class account_journal(models.Model):
    _inherit = "account.journal"

    sucursal_id = fields.Many2one(
            'sii.sucursal',
            string="Sucursal",
        )
    sii_code = fields.Char(
            string="Código SII Sucursal",
            readonly=True,
        )
    journal_document_class_ids = fields.Char("journal_document_class_ids")
    use_documents = fields.Boolean(
            string='Use Documents?',
            default='_get_default_doc',
        )
    journal_activities_ids = fields.Char("journal_activities_ids")
    restore_mode = fields.Boolean(
            string="Restore Mode",
            default=False,
        )
    send_book_dte = fields.Boolean(
            string="¿No Enviar los libros de Compra/Venta al SII?",
            help="Para saber si se envian los Libros Fiscales al SII o se mantienen para control interno de la empresa.",
            store=True,
        )

    @api.onchange('journal_activities_ids')
    def max_actecos(self):
        if len(self.journal_activities_ids) > 4:
            raise UserError("Deben Ser máximo 4 actecos por Diario, seleccione los más significativos para este diario")

    # @api.multi
    def _get_default_doc(self):
        self.ensure_one()
        if self.type == 'sale' or self.type == 'purchase':
            self.use_documents = True

    # @api.multi
    def name_get(self):
        res = []
        for journal in self:
            currency = journal.currency_id or journal.company_id.currency_id
            name = "%s (%s)" % (journal.name, currency.name)
            if journal.sucursal_id and self.env.context.get('show_full_name', False):
                name = "%s (%s)" % (name, journal.sucursal_id.name)
            res.append((journal.id, name))
        return res
