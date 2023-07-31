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

    def name_get(self):
        result = []
            
            
        for rec in self:
            if rec.name:
                result.append((rec.id, '[%s] %s' % (rec.name,rec.full_address)))
            else:
                result.append((rec.id, '%s' % (rec.full_address)))
        return result

    @api.model
    def create(self, values):
        """Override default Odoo create function and extend."""
        try:
            here_api_key = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.here_api_key')
            request = "https://geocode.search.hereapi.com/v1/geocode?q=%s&apiKey=%s" % (values['full_address'], here_api_key)
            request_get = get(url = request)
            requests_result = request_get.json()
            if requests_result['items']:
                values['longitude'] = requests_result['items'][0]['position']['lng']
                values['latitude'] = requests_result['items'][0]['position']['lat']
                values['full_address'] = requests_result['items'][0]['address']['label']
        except:
            pass
        return super(PointOfInterest, self).create(values)

    def write(self, values):
        """Override default Odoo write function and extend."""
        if 'full_address' in values:
            try:
                here_api_key = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.here_api_key')
                request = "https://geocode.search.hereapi.com/v1/geocode?q=%s&apiKey=%s" % (values['full_address'], here_api_key)
                request_get = get(url = request)
                requests_result = request_get.json()
                print(requests_result)
                if requests_result['items']:
                    values['longitude'] = requests_result['items'][0]['position']['lng']
                    values['latitude'] = requests_result['items'][0]['position']['lat']
                    values['full_address'] = requests_result['items'][0]['address']['label']
            except:
                pass
        return super(PointOfInterest, self).write(values)