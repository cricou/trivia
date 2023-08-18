# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

STATE=[
    ('draft', "Draft"),
    ('in_progress', "In progress"),
    ('done', "Done")
]

class TriviaTourPlan(models.Model):
    _name = 'trivia.tour.plan'
    _description = 'TRIVIA Tour plan'
    _inherit = ['mail.thread']

    name = fields.Char(string="Name", copy=False, readonly=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    mission_order_ids = fields.Many2many('mission.order', string="Missions order")
    tour_plan_fleet_ids = fields.One2many('trivia.tour.plan.fleet', 'tour_plan_id')
    
    note = fields.Text(string="Note")

    tour_ids = fields.One2many('trivia.tour', 'tour_plan_id')
    tour_count = fields.Integer(compute='_calc_tour_count')

    @api.model
    def create(self, values):
        if not values.get('name'):
            # fallback on any pos.order sequence
            values['name'] = self.env['ir.sequence'].next_by_code('trivia_tms.tour_plan')
        return super(TriviaTourPlan, self).create(values)

    def _calc_tour_count(self):
        self.ensure_one()
        for rec in self:
            rec.tour_count = len(rec.tour_ids)

    def open_tour(self):
        return {
            'name': 'Tour',
            'domain': [('tour_plan_id', '=', self.id)],
            'res_model': 'trivia.tour',
            'target': 'current',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }