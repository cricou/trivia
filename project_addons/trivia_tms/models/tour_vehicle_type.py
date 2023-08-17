from odoo import api, fields, models, _

class TriviaTourVehicleType(models.Model):
    _name = 'trivia.tour.vehicle.type'
    _description = 'TRIVIA Tour Vehicle Type'

    name = fields.Char(sting="Name")
    profile_id = fields.Many2one('trivia.tour.profile')
    fixed_cost = fields.Float(string="Fixed Cost")
    distance_cost = fields.Float(string="Distance Cost")
    time_cost = fields.Float(string="Time Cost")
    capacity = fields.Char("Capacity")
    skill_ids = fields.Many2many('trivia.tour.skill')
    vehicle_ids = fields.One2many('fleet.vehicle', 'tour_vehicle_type_id', string="Vehicles")