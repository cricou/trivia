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


class TriviaTourStepActivity(models.Model):
    _name = 'trivia.tour.step.activity'
    _description = 'TRIVIA Tour Step'
    _inherit = ['mail.thread']
    _order = 'sequence'

    name = fields.Char(string="Name", compute='_compute_name', store="True")
    sequence = fields.Integer(string="Sequence")
    mission_order_id = fields.Many2one('mission.order')
    full_address = fields.Char(string="Full Address")
    activity_type = fields.Selection(selection=ACTIVITY_TYPE, string="Activity")
    distance = fields.Float(string="Distance")
    load = fields.Char(stirng="Load")
    arrival_date = fields.Datetime(string="Arrival Date")
    departure_date = fields.Datetime(string="Departure Date")
    note = fields.Text(string="Note")
    state = fields.Selection(selection=STATE, default='draft')
    tour_step_id = fields.Many2one('trivia.tour.step', string="Tour Step")

    # @api.depends('activity_type', 'full_address')
    # def _compute_name(self):
    #     for rec in self:
    #         if rec.full_address:
    #             rec.name = "%s - %s" % (rec.activity_type,rec.full_address)