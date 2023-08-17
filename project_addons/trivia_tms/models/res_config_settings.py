# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    here_api_key = fields.Char(string='Here API KEY',
                               config_parameter="trivia_tms.here_api_key")
    here_oauth_key_id = fields.Char(string='Here OAuth KEY ID',
                                    config_parameter="trivia_tms.here_oauth_key_id")
    here_oauth_secret_id = fields.Char(string='Here OAuth SECRET ID',
                                       config_parameter="trivia_tms.here_oauth_secret_id")
    truck_fuel_consumption = fields.Float(string="Truck Fuel Consumption",
                                          default=35,
                                          config_parameter="trivia_tms.truck_fuel_consumption")
    fuel_cost = fields.Float(string="Fuel Cost",
                            default=1.70,
                            config_parameter="trivia_tms.fuel_cost")

    tp_shift_start = fields.Float(string="Shift Start",
                                  config_parameter="trivia_tms.tp_shift_start")
    tp_shift_end = fields.Float(string="Shift End",
                                config_parameter="trivia_tms.tp_shift_end")
    tp_shift_location_start = fields.Many2one('point.of.interest', 
                                              string="Location",
                                              config_parameter='trivia_tms.tp_shift_location_start')
    tp_shift_location_end = fields.Many2one('point.of.interest',
                                            string="Location",
                                            config_parameter='trivia_tms.tp_shift_location_end')
    tp_shift_offset_start = fields.Float(string="Departure Time Offset",
                                        config_parameter='trivia_tms.tp_shift_offset_start')
    tp_shift_time = fields.Float(string="Shift Time",
                                config_parameter='trivia_tms.tp_shift_time')
    tp_break_timewindow_start = fields.Float(string="Break Timewindow Start",
                                            config_parameter='trivia_tms.tp_break_timewindow_start')
    tp_break_timewindow_end = fields.Float(string="Break Timewindow End",
                                          config_parameter='trivia_tms.tp_break_timewindow_end')
    tp_break_duration = fields.Float(String="Break Duration",
                                     config_parameter='trivia_tms.tp_break_duration')
    
    

