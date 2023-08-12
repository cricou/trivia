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

    name = fields.Char(string="Name", compute='_compute_name', store="True")
    sequence = fields.Integer(string="Sequence")
    tour_id = fields.Many2one('trivia.tour')
    mission_order_id = fields.Many2one('mission.order')
    activity_type = fields.Selection(selection=ACTIVITY_TYPE, string="Activity")
    distance = fields.Float(string="Distance")
    cargo_length = fields.Float(string="Cargo Length", related='mission_order_id.cargo_length')
    cargo_payload = fields.Float(string="Cargo Payload", related='mission_order_id.cargo_payload')
    reserved_length = fields.Float(string="Reserved Length")
    reserved_payload = fields.Float(string="Reserved Payload")
    arrival_date = fields.Datetime(string="Arrival Date")
    departure_date = fields.Datetime(string="Departure Date")
    full_address = fields.Char(string="Full Address")
    note = fields.Text(string="Note")
    state = fields.Selection(selection=STATE, default='draft')
    vehicle_id = fields.Many2one('fleet.vehicle')

    @api.depends('activity_type', 'full_address')
    def _compute_name(self):
        for rec in self:
            if rec.full_address:
                rec.name = "%s - %s" % (rec.activity_type,rec.full_address)

    @api.onchange('mission_order_id', 'activity_type')
    def _get_full_address(self):
        if self.mission_order_id and self.activity_type:
            if self.activity_type == 'pickup':
                self.full_address = self.mission_order_id.loading.full_address
            elif self.activity_type == 'delivery':
                self.full_address = self.mission_order_id.delivery.full_address
            else:
                self.full_address = None