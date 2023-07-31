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