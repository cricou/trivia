from odoo import api, fields, models, _

class TriviaTrackingLocation(models.Model):
    _name = 'trivia.tracking.location'
    _description = 'TRIVIA Tracking location'

    user_id = fields.Many2one('res.users')
    latitude = fields.Float(digits=(12, 7))
    longitude = fields.Float(digits=(12, 7))
    altitude = fields.Float()
    bearing = fields.Float()
    speed = fields.Float()
    time = fields.Datetime()
    accuracy = fields.Float()
