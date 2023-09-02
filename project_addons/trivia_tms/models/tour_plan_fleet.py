# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import pytz
from datetime import date, timedelta, datetime
from odoo.addons.trivia_tms.tutils import Tutils


class TriviaTourPlanFleet(models.Model):
    _name = 'trivia.tour.plan.fleet'
    _description = 'TRIVIA Tour plan fleet'

    def get_default_shift_time(self):
            return self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_shift_time')

    def get_default_tour_plan_fleet_shift_ids(self):
        tz = self.env.context.get('tz')
        parent_id = self.env['trivia.tour.plan'].search([('id', '=', self.env.context.get('parent_id'))])
        end_date = parent_id.end_date
        start_date = parent_id.start_date

        shift_start = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_shift_start')
        shift_end = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_shift_end')
        start_delta = timedelta(seconds=int(Tutils.convert_float_time_to_second(float(shift_start))))
        end_delta = timedelta(seconds=int(Tutils.convert_float_time_to_second(float(shift_end))))

        shift_location_start = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_shift_location_start')
        shift_location_start_id = self.env['point.of.interest'].search([('id', '=', shift_location_start)])
        shift_location_end = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_shift_location_end')
        shift_location_end_id = self.env['point.of.interest'].search([('id', '=', shift_location_end)])

        shift_offset_start = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_shift_offset_start')

        shift_break_start = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_break_timewindow_start')
        shift_break_end = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_break_timewindow_end')
        shift_break_duration = float(self.env['ir.config_parameter'].sudo().get_param('trivia_tms.tp_break_duration'))
        break_start_delta = timedelta(seconds=int(Tutils.convert_float_time_to_second(float(shift_break_start))))
        break_end_delta = timedelta(seconds=int(Tutils.convert_float_time_to_second(float(shift_break_end))))

    
        values = []
        for single_date in Tutils.daterange(start_date, end_date):
            datetime_day = datetime.combine(single_date, datetime.min.time())
            datetime_shift_start = datetime_day + start_delta
            datetime_shift_start = Tutils.convert_local_datetime_to_utc_date_time(datetime_shift_start, tz)
            datetime_shift_end = datetime_day + end_delta
            datetime_shift_end = Tutils.convert_local_datetime_to_utc_date_time(datetime_shift_end, tz)

            datetime_shift_break_start = datetime_day + break_start_delta
            datetime_shift_break_start = Tutils.convert_local_datetime_to_utc_date_time(datetime_shift_break_start, tz)
            datetime_shift_break_end = datetime_day + break_end_delta
            datetime_shift_break_end = Tutils.convert_local_datetime_to_utc_date_time(datetime_shift_break_end, tz)

            values.append(
                (0, 0, {
                    'start_date': datetime_shift_start,
                    'end_date': datetime_shift_end,
                    'shift_offset_start': shift_offset_start,
                    'shift_location_start': shift_location_start_id,
                    'shift_location_end': shift_location_end_id,
                    'break_start_date': datetime_shift_break_start,
                    'break_end_date': datetime_shift_break_end,
                    'break_duration': shift_break_duration
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
    tour_plan_fleet_shift_ids = fields.One2many('trivia.tour.plan.fleet.shift',
                                                'tour_plan_fleet_id',
                                                default=get_default_tour_plan_fleet_shift_ids)
    
    _sql_constraints = [
        ('unique_tour_plan_fleet', 'UNIQUE(tour_plan_id, is_external_fleet, tour_vehicle_type_id)', 'Combination of Tour Plan, External Fleet, and Vehicle Type must be unique.')
    ]

    
