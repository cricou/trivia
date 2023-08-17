from odoo import api, fields, models, _

TRIVIA_PRFILE_TYPE=[
    ('car', "Car"),
    ('truck', "Truck"),
    ('bus', "Bus"),
    ('privateBus', "Private Bus"),
    ('bicycle', "Bicycle"),
    ('scooter', "Scooter"),
    ('pedestrian', "Pedestrian")
]


class TriviaTourProfile(models.Model):
    _name = 'trivia.tour.profile'
    _description = 'TRIVIA Profile'

    name = fields.Char(sting="Name")
    profile_type = fields.Selection(selection=TRIVIA_PRFILE_TYPE, string="Profile")