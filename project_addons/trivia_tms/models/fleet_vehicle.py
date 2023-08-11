from odoo import api, fields, models, _

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    semi_trailer_id = fields.Many2one('trivia.semi.trailer')