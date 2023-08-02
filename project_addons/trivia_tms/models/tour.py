# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from requests import get, post, HTTPError
import json
from json import dumps
import http.client
import urllib.parse


class TriviaTour(models.Model):
    _name = 'trivia.tour'
    _description = 'TRIVIA Tour'

    name = fields.Char(string="Name", copy=False, readonly=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    mission_order_ids = fields.Many2many('mission.order', string="Missions order")

    note = fields.Text(string="Note")

    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    driver_id = fields.Many2one('res.partner', related='vehicle_id.driver_id')
    
    driving_time = fields.Float(string="Driving time")
    distance = fields.Float(string="Distance")
    fuel_cost = fields.Float(string="Fuel cost")
    toll_cost = fields.Float(string="Tolls cost")
    total_cost = fields.Float(string="Total cost")
    includes_ferry = fields.Boolean(string = "Includes Ferry")
    ferry_time = fields.Float(string="Ferry time")
    
    @api.model
    def create(self, values):
        if not values.get('name'):
            # fallback on any pos.order sequence
            values['name'] = self.env['ir.sequence'].next_by_code('trivia_tms.tour')
        return super(TriviaTour, self).create(values)

    def calc_full_routes(self):
        here_api_key = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.here_api_key')
        truck_fuel_consumption = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.truck_fuel_consumption')
        fuel_cost = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.fuel_cost')
        mo_len = len(self.mission_order_ids) - 1
        origin = ""
        waypoints = ""
        destination = ""
        i = 0
        if mo_len == 0:
                origin = str(self.mission_order_ids[i].loading.latitude) + "," + str(self.mission_order_ids[i].loading.longitude)
                destination = str(self.mission_order_ids[i].delivery.latitude) + "," + str(self.mission_order_ids[i].delivery.longitude)
        else:
            while i <= mo_len:
                if not origin:
                    origin = str(self.mission_order_ids[i].loading.latitude) + "," + str(self.mission_order_ids[i].loading.longitude)
                    waypoints += str(self.mission_order_ids[i].delivery.latitude) + "," + str(self.mission_order_ids[i].delivery.longitude)
                elif origin and i != mo_len:
                    if self.mission_order_ids[i-1].delivery.full_address == self.mission_order_ids[i].loading.full_address:
                        waypoints +=  "&via=" + str(self.mission_order_ids[i].delivery.latitude) + "," + str(self.mission_order_ids[i].delivery.longitude)
                    else:
                        waypoints += "&via=" + str(self.mission_order_ids[i].loading.latitude) + "," + str(self.mission_order_ids[i].loading.longitude) + "&via=" + str(self.mission_order_ids[i].delivery.latitude) + "," + str(self.mission_order_ids[i].delivery.longitude)
                elif origin and i == mo_len:
                    if self.mission_order_ids[i-1].delivery.full_address == self.mission_order_ids[i].loading.full_address:
                        pass
                    else:
                        waypoints += "&via=" + str(self.mission_order_ids[i].loading.latitude) + "," + str(self.mission_order_ids[i].loading.longitude)
                    destination = str(self.mission_order_ids[i].delivery.latitude) + "," + str(self.mission_order_ids[i].delivery.longitude)
                i+=1
        if waypoints:
            request = "https://router.hereapi.com/v8/routes?apikey=%s&origin=%s&destination=%s&via=%s&return=summary,tolls&transportMode=truck&currency=EUR&truck[grossWeight]=12000&truck[height]=400" % (here_api_key, origin, destination, waypoints)
        else:
            request = "https://router.hereapi.com/v8/routes?apikey=%s&origin=%s&destination=%s&return=summary,tolls&transportMode=truck&currency=EUR&truck[grossWeight]=12000&truck[height]=400" % (here_api_key, origin, destination)
        request_get = get(url = request)
        requests_result = request_get.json()
        driving_time = 0
        distance_km = 0
        toll_cost = 0
        ferry_time = 0
        includes_ferry = False
        for section in requests_result['routes'][0]["sections"]:
            if section.get('tolls'):
                for toll in section["tolls"]:
                    toll_cost += toll['fares'][0]['convertedPrice']['value']
            if section['transport']['mode'] in ['truck', 'carShuttleTrain']:
                driving_time += section['summary']["duration"] / 60 / 60
                distance_km += section['summary']["length"] / 1000
            if section['transport']['mode'] in ['ferry']:
                ferry_time += section['summary']["duration"] / 60 / 60
                includes_ferry = True
            
        self.toll_cost = toll_cost
        self.fuel_cost = float(distance_km) * float(truck_fuel_consumption) / 100 * float(fuel_cost)
        self.total_cost = self.toll_cost + self.fuel_cost
        self.distance = round(float(distance_km),2)
        self.driving_time = float(driving_time)
        self.ferry_time = float(ferry_time)
        self.includes_ferry = includes_ferry

    def google_map_url(self):
        if self.id:
            
            mo_len = len(self.mission_order_ids) - 1
            origin = ""
            waypoints = ""
            destination = ""
            i = 0
            if mo_len == 0:
                origin = self.mission_order_ids[i].loading.full_address
                destination = self.mission_order_ids[i].delivery.full_address
            else:
                while i <= mo_len:
                    print(self.mission_order_ids[i])
                    if not origin:
                        origin = self.mission_order_ids[i].loading.full_address
                        waypoints += self.mission_order_ids[i].delivery.full_address
                    elif origin and i != mo_len:
                        if self.mission_order_ids[i-1].delivery.full_address == self.mission_order_ids[i].loading.full_address:
                            waypoints +=  "|" + self.mission_order_ids[i].delivery.full_address
                        else:
                            waypoints += "|" + self.mission_order_ids[i].loading.full_address + "|" + self.mission_order_ids[i].delivery.full_address
                    elif origin and i == mo_len:
                        if self.mission_order_ids[i-1].delivery.full_address == self.mission_order_ids[i].loading.full_address:
                            pass
                        else:
                            waypoints += "|" + self.mission_order_ids[i].loading.full_address
                        destination = self.mission_order_ids[i].delivery.full_address
                    i+=1
            
            origin = urllib.parse.quote_plus(origin)
            waypoints = urllib.parse.quote_plus(waypoints)
            destination = urllib.parse.quote_plus(destination)

            if waypoints:
                google_map_url = "https://www.google.com/maps/dir/?api=1&origin=%s&waypoints=%s&destination=%s&travelmode=driving&hl=fr" % (origin, waypoints, destination)
            else:
                google_map_url = "https://www.google.com/maps/dir/?api=1&origin=%s&destination=%s&travelmode=driving&hl=fr" % (origin, destination)
           
            return {
                'type': 'ir.actions.act_url',
                'url': google_map_url,
                'target': 'new',
            }