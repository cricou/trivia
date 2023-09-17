from odoo import models, fields

class ResUsersInherited(models.Model):
    _inherit = 'res.users'

    one_signal_subscription_ids = fields.One2many(
        'trivia.one.signal.subscription',  # Nom du modèle cible
        'user_id',                          # Champ Many2one dans trivia.one.signal.subscription
        string='OneSignal Subscriptions'    # Libellé du champ
    )

    trivia_app_ids = fields.One2many(
        'trivia.app',                       # Nom du modèle cible
        'user_id',                          # Champ Many2one dans trivia.app
        string='Trivia Apps'                 # Libellé du champ
    )
    one_signal_subscription_count = fields.Integer(compute='_calc_one_signal_subscription_count')
    app_count = fields.Integer(compute='_calc_app_count')

    def _calc_one_signal_subscription_count(self):
        self.ensure_one()
        for rec in self:
            rec.one_signal_subscription_count = len(rec.one_signal_subscription_ids)

    def open_one_signal_subscription(self):
        return {
            'name': 'One Signal Subscriptions',
            'domain': [('user_id', '=', self.id)],
            'res_model': 'trivia.one.signal.subscription',
            'target': 'current',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }
    
    def _calc_app_count(self):
        self.ensure_one()
        for rec in self:
            rec.app_count = len(rec.trivia_app_ids)

    def open_app(self):
        return {
            'name': 'App',
            'domain': [('user_id', '=', self.id)],
            'res_model': 'trivia.app',
            'target': 'current',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }