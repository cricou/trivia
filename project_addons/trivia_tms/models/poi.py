# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from requests import get, post, HTTPError
import json
from json import dumps
import http.client


class PointOfInterest(models.Model):
    _name = 'point.of.interest'
    _description = 'Point Of Interest'
    _rec_name = 'full_address'

    name = fields.Char(string="Name")
    full_address = fields.Char(string="Full Address")
    longitude = fields.Float(string="Longitude")
    latitude = fields.Float(string="Latitude")

    @api.onchange('full_address')
    def get_coordinate(self):
        here_api_key = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.here_api_key')
        request = "https://geocode.search.hereapi.com/v1/geocode?q=%s&apiKey=%s" % (self.full_address, here_api_key)
        request_get = get(url = request)
        requests_result = request_get.json()
        print(requests_result)
        self.longitude = requests_result['items'][0]['position']['lng']
        self.latitude = requests_result['items'][0]['position']['lat']
        self.full_address = requests_result['items'][0]['address']['label']
