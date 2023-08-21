# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class TriviaTourPlanFleetShift(models.Model):
    _name = 'trivia.tour.plan.fleet.shift'
    _description = 'TRIVIA Tour plan fleet shift'

    start_date = fields.Datetime(string='Start')
    end_date = fields.Datetime(string='End ')
    break_start_date = fields.Datetime(string='Break Start')
    break_end_date = fields.Datetime(string='Break End')
    break_duration = fields.Float(string="Break Duration")
    tour_plan_fleet_id = fields.Many2one('trivia.tour.plan.fleet')
    shift_offset_start = fields.Float(string="Departure Time Offset")
    shift_location_start = fields.Many2one('point.of.interest',
                                            string="Start Location")
    shift_location_end = fields.Many2one('point.of.interest',
                                          string="End Location")