# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import pytz
from datetime import date, timedelta, datetime

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
    
    def daterange(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)
            
    def convert_float_time_to_second(self, float_time):

        hours = int(float_time) 
        minutes_decimal = float_time - hours
        minutes = int(minutes_decimal * 60)

        total_seconds = (hours * 3600) + (minutes * 60)

        return total_seconds

    def get_default_tour_plan_fleet_shift_ids(self):
        tz = self.env.context.get('tz')
        local_timezone = pytz.timezone(tz)
        parent_id = self.env['trivia.tour.plan'].search([('id', '=', self.env.context.get('parent_id'))])
        end_date = parent_id.end_date
        start_date = parent_id.start_date
        shift_start = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_shift_start')
        shift_end = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_shift_end')
        start_delta = timedelta(seconds=int(self.convert_float_time_to_second(float(shift_start))))
        end_delta = timedelta(seconds=int(self.convert_float_time_to_second(float(shift_end))))
        shift_location_start = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_shift_location_start')
        shift_location_start_id = self.env['point.of.interest'].search([('id', '=', shift_location_start)])
        shift_location_end = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_shift_location_end')
        shift_location_end_id = self.env['point.of.interest'].search([('id', '=', shift_location_end)])
        shift_offset_start = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_shift_offset_start')
    
        values = []
        for single_date in self.daterange(start_date, end_date):
            datetime_day = datetime.combine(single_date, datetime.min.time())
            datetime_shift_start = datetime_day + start_delta
            datetime_shift_start = local_timezone.localize(datetime_shift_start)
            datetime_shift_start = datetime_shift_start.astimezone(pytz.utc)
            datetime_shift_start = datetime_shift_start.replace(tzinfo=None)
            datetime_shift_end = datetime_day + end_delta
            datetime_shift_end = local_timezone.localize(datetime_shift_end)
            datetime_shift_end = datetime_shift_end.astimezone(pytz.utc)
            datetime_shift_end = datetime_shift_end.replace(tzinfo=None)
          
            print(datetime_shift_start)
            values.append(
                (0, 0, {
                    'start_date': datetime_shift_start,
                    'end_date': datetime_shift_end,
                    'shift_offset_start': shift_offset_start,
                    'shift_location_start': shift_location_start_id,
                    'shift_location_end': shift_location_end_id
                })
            )
        return values

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

    
