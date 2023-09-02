from odoo import api, fields, models, _

MO_STATUS=[
    ('draft', "Draft"),
    ('in_progress', "In progress"),
    ('done', "Done")
]

class TriviaSemiTrailer(models.Model):
    _name = 'trivia.semi.trailer'
    _description = 'TRIVIA Semi Trailer'
    _rec_name = "licence_plate"

    licence_plate = fields.Char(string="Licence Plate")
    payload_capacity = fields.Integer(string="Payload Capacity")
    number_of_axles = fields.Integer(string="Number Of Axles")
    internal_length = fields.Float(string="Internal Length")
    internal_width = fields.Float(string="Internal Width")
    internal_height = fields.Float(string="Internal Height")