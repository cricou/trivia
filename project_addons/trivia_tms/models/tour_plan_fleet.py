# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import datetime

class TriviaTourPlanFleet(models.Model):
    _name = 'trivia.tour.plan.fleet'
    _description = 'TRIVIA Tour plan fleet'

    def get_default_shift_time(self):
            return self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_shift_time')

    def get_default_break_timewindow_start(self):
            return self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_break_timewindow_start')

    def get_default_break_timewindow_end(self):
            return self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_break_timewindow_end')

    def get_default_break_duration(self):
            return self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_break_duration')
    
    def get_default_tour_plan_fleet_shift_ids(self):
        parent_id = self.env['trivia.tour.plan'].search([('id', '=', self.env.context.get('parent_id'))])
        test = self.write({

                    'tour_plan_fleet_shift_ids': [(0,0, {
                                                'start_date':parent_id.start_date
                                                   })]
                                })
        print("rererer")
        print(test)

    name = fields.Char(string="Name")
    tour_plan_id = fields.Many2one('trivia.tour.plan')
    tour_vehicle_type_id = fields.Many2one('trivia.tour.vehicle.type')
    tour_profile_id = fields.Many2one(related='tour_vehicle_type_id.tour_profile_id')
    is_external_fleet = fields.Boolean()
    vehicle_ids = fields.Many2many('fleet.vehicle')
    vehicle_amount = fields.Integer(string="Vehicle Amount")
    shift_time = fields.Float(string="Shift time", 
                              default=get_default_shift_time)
    stop_base_duration = fields.Integer(string="Stop base duration")
    break_timewindow_start = fields.Float(string="Break Time Start", 
                                          default=get_default_break_timewindow_start)
    break_timewindow_end = fields.Float(string="Break Time End", 
                                        default=get_default_break_timewindow_end)
    break_duration = fields.Float(String="Break Duration", 
                                  default=get_default_break_duration)
    tour_plan_fleet_shift_ids = fields.One2many('trivia.tour.plan.fleet.shift',
                                                'tour_plan_fleet_id',
                                                default=get_default_tour_plan_fleet_shift_ids)

    
