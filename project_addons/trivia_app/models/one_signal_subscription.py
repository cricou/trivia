from odoo import models, fields

class TriviaOneSignalSubscription(models.Model):
    _name = 'trivia.one.signal.subscription'
    _description = 'One Signal Subscriptions'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True
    )
    subscription_ref = fields.Char()
    one_signal_ref = fields.Char()
    