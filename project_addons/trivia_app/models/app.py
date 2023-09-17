from odoo import models, fields

class TriviaApp(models.Model):
    _name = 'trivia.app'
    _description = 'Trivia Apps'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True
    )
    unique_app_ref = fields.Char()