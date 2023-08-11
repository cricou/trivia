from odoo import api, fields, models, _

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    semi_trailer_id = fields.Many2one('trivia.semi.trailer')


class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    vehicle_type = fields.Selection(selection=[('car', "Car"), ('bike', "Bike"), ('truck', "Truck")])
