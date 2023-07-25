# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from requests import get, post, HTTPError
from requests_oauthlib import OAuth1
import json
from json import dumps
import http.client
import time

MO_STATUS=[
    ('draft', "Draft"),
    ('in_progress', "In progress"),
    ('done', "Done")
]

class MissionOrder(models.Model):
    _name = 'mission.order'
    _description = 'Mission Order'
    _inherit = ['mail.thread']

    name = fields.Char(string="Name",
                       default=lambda self: self.env['ir.sequence'].next_by_code('trivia_tms.mission.order'))
    date = fields.Date(string="Order date",
                       default=lambda self: fields.Date.today())
    driver = fields.Many2one('res.partner', string="Driver")
    loading = fields.Many2one('point.of.interest', string="Loading")
    loading_date = fields.Datetime(string="Loading date")
    delivery = fields.Many2one('point.of.interest', string="Delivery")
    delivery_date = fields.Datetime(string="Delivery date")
    note = fields.Text(string="Note")
    state = fields.Selection(selection=MO_STATUS, default="draft")
    #Route
    driving_time = fields.Float(string="Driving time")
    distance = fields.Float(string="Distance")
    fuel_cost = fields.Float(string="Fuel cost")
    toll_cost = fields.Float(string="Tolls cost")
    total_cost = fields.Float(string="Total cost")

    def calc_routes(self):
        pass
        here_api_key = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.here_api_key')
        truck_fuel_consumption = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.truck_fuel_consumption')
        print(truck_fuel_consumption)

        origin_coordinate = str(self.loading.latitude) + "," + str(self.loading.longitude)
        destination_coordinate = str(self.delivery.latitude) + "," + str(self.delivery.longitude)
        
        request = "https://router.hereapi.com/v8/routes?apikey=" + here_api_key + "&origin=" + origin_coordinate + "&destination=" + destination_coordinate + "&return=summary,tolls&transportMode=truck&currency=EUR&truck[grossWeight]=12000&truck[height]=400"
        request_get = get(url = request)
        requests_result = request_get.json()
        print(requests_result)
        driving_time = requests_result['routes'][0]["sections"][0]['summary']["duration"] / 60 / 60
        distance_km = requests_result['routes'][0]["sections"][0]['summary']["length"] / 1000

        if requests_result['routes'][0]["sections"][0].get('tolls'):
            toll_cost = 0
            for toll in requests_result['routes'][0]["sections"][0]["tolls"]:
                toll_cost += toll['fares'][0]['convertedPrice']['value']
        self.toll_cost = toll_cost
        self.fuel_cost = float(distance_km) * float(truck_fuel_consumption) / 100 * 1.91
        self.total_cost = self.toll_cost + self.fuel_cost
        self.distance = round(float(distance_km),2)
        self.driving_time = float(driving_time)

