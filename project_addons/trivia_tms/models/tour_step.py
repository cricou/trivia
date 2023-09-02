# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

ACTIVITY_TYPE=[
    ('departure', "Departure"),
    ('arrival', "Arrival"),
    ('pickup', "Pickup"),
    ('delivery', "Delivery"),
    ('break', "Break"),
    ('reload', "Reload")
]

STATE=[
    ('draft', "Draft"),
    ('in_progress', "In progress"),
    ('done', "Done")
]

class TriviaTourStep(models.Model):
    _name = 'trivia.tour.step'
    _description = 'TRIVIA Tour Step'
    _inherit = ['mail.thread']
    _order = 'sequence'

    name = fields.Char(string="Name")
    sequence = fields.Integer(string="Sequence")
    tour_id = fields.Many2one('trivia.tour')
    distance = fields.Float(string="Distance")
    load = fields.Char(stirng="Load")
    arrival_date = fields.Datetime(string="Arrival Date")
    departure_date = fields.Datetime(string="Departure Date")
    location_id = fields.Many2one('point.of.interest', string="Location")
    note = fields.Text(string="Note")
    state = fields.Selection(selection=STATE, default='draft')
    tour_step_activity_ids = fields.One2many('trivia.tour.step.activity', 'tour_step_id')

    tour_step_activity_type_ids = fields.Many2many('trivia.tour.step.activity.type')

    @api.onchange('mission_order_id', 'activity_type')
    def _get_full_address(self):
        if self.mission_order_id and self.activity_type:
            if self.activity_type == 'pickup':
                self.full_address = self.mission_order_id.loading.full_address
            elif self.activity_type == 'delivery':
                self.full_address = self.mission_order_id.delivery.full_address
            else:
                self.full_address = None