# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from requests import get, post, HTTPError, utils
import json
from json import dumps
import http.client
import urllib.parse
import base64
import hmac
import hashlib
import random
import time

class TriviaTour(models.Model):
    _name = 'trivia.tour'
    _description = 'TRIVIA Tour'
    _inherit = ['mail.thread']

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

    tour_step_ids = fields.One2many('trivia.tour.step', 'tour_id', string="Tour Steps")
    tour_step_count = fields.Integer(compute='_calc_tour_step_count')

    def _calc_tour_step_count(self):
        self.ensure_one()
        for rec in self:
            rec.tour_step_count = len(rec.tour_step_ids)

    def open_tour_step(self):
        return {
            'name': 'Tour Steps',
            'domain': [('tour_id', '=', self.id)],
            'res_model': 'trivia.tour.step',
            'target': 'current',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }

    @api.model
    def create(self, values):
        if not values.get('name'):
            # fallback on any pos.order sequence
            values['name'] = self.env['ir.sequence'].next_by_code('trivia_tms.tour')
        return super(TriviaTour, self).create(values)

    def getAuthToken(self):
        access_key = "mxg_lw8VElp8LZyVcrAQ0Q"
        access_secret = "ruSop9w5cuDfIAx-0yz-PZl6Sfg3-oe8vXvP1f31m6EyWS2_xl6ELW7zgTLJJ8xMarDn_4Nn7_Q5HMsagmt5Lw"
        scope = "hrn:here:authorization::org779535579:project/1652447479575"

        url = "https://account.api.here.com/oauth2/token"  # Remplacez par l'URL réelle de votre endpoint

        # Génération d'une chaîne aléatoire pour oauth_nonce
        oauth_nonce = ''.join([random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(32)])

        # Calcul du timestamp
        oauth_timestamp = str(int(time.time()))

        # Création des paramètres OAuth
        oauth_params = {
            "grant_type": "client_credentials",
            "oauth_consumer_key": access_key,
            "oauth_nonce": oauth_nonce,
            "oauth_signature_method": "HMAC-SHA256",
            "oauth_timestamp": oauth_timestamp,
            "oauth_version": "1.0",
            "scope": scope
        }
        

        # Tri des paramètres OAuth par clé
        sorted_params = sorted(oauth_params.items(), key=lambda x: x[0])

        # Création de la chaîne de paramètres encodée pour la signature
        param_string = "&".join([f"{param}={urllib.parse.quote(value, safe='')}" for param, value in sorted_params])
        base_string = f"POST&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(param_string, safe='')}"
        key = f"{urllib.parse.quote(access_secret, safe='')}&"

        # Création de la signature OAuth
        signature = base64.b64encode(hmac.new(key.encode(), base_string.encode(), hashlib.sha256).digest()).decode()

        # Ajout de la signature aux paramètres OAuth
        oauth_params["oauth_signature"] = signature

        # Création de l'en-tête d'autorisation
  
        oauth_params_header = {
            "oauth_consumer_key": access_key,
            "oauth_signature_method": "HMAC-SHA256",
            "oauth_timestamp": oauth_timestamp,
            "oauth_nonce": oauth_nonce,
            "oauth_version": "1.0",
            "oauth_signature": signature
        }

        auth_header = ", ".join([f'{param}="{urllib.parse.quote(value, safe="")}"' for param, value in oauth_params_header.items()])
   
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
            "Authorization": f'OAuth {auth_header}',
            "Host": "account.api.here.com"
        }

        # Préparation des données du corps de la requête
        body = {
            "grant_type": "client_credentials",
            "scope": scope
        }

        # Envoi de la requête POST
        response = post(url, data=body, headers=headers)
        print(response.status_code)
        print(response.text)
        if response.status_code == 200:
            token_json = response.json()
            return token_json["access_token"]

    def calc_full_routes(self):
        token = self.getAuthToken()
        print(token)
        # get signature
        truck_fuel_consumption = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.truck_fuel_consumption')
        fuel_cost = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.fuel_cost')
        # Define new data to create

        # encoded_url = """grant_type=client_credentials&scope=hrn:here:authorization::org779535579:project/1652447479575&oauth_consumer_key=mxg_lw8VElp8LZyVcrAQ0Q&oauth_nonce=LIIpk4&oauth_signature_method=HMAC-SHA256&oauth_timestamp=1456945283&oauth_version=1.0"""
        # encoded_url = urllib.parse.quote_plus(encoded_url)

        # print(token.json())
        body = {
                "plan": {
                    "jobs": [
                    {
                        "id": "myJob",
                        "tasks": {
                        "deliveries": [
                            {
                            "places": [
                                {
                                "location": {"lat": 52.46642, "lng": 13.28124},
                                "times": [["2023-08-11T10:00:00.000Z","2023-08-11T12:00:00.000Z"]],
                                "duration": 180
                                }
                            ],
                            "demand": [1]
                            }
                        ]
                        }
                    }
                    ]
                },
                "fleet": {
                    "types": [
                    {
                        "id": "myVehicleType",
                        "profile": "normal_car",
                        "costs": {
                        "distance": 0.0002,
                        "time": 0.005,
                        "fixed": 22
                        },
                        "shifts": [{
                        "start": {
                            "time": "2023-08-11T09:00:00Z",
                            "location": {"lat": 52.52568, "lng": 13.45345}
                        },
                        "end": {
                            "time": "2023-08-11T18:00:00Z",
                            "location": {"lat": 52.52568, "lng": 13.45345}
                        }
                        }],
                        "limits": {
                        "maxDistance": 300000,
                        "shiftTime": 28800
                        },
                        "capacity": [10],
                        "amount": 1
                    }
                    ],
                    "profiles": [{
                    "name": "normal_car",
                    "type": "car",
                    "departureTime": "2023-08-11T09:15:00Z"
                    }]
                },
                "configuration": {
                    "termination": {
                    "maxTime": 2,
                    "stagnationTime": 1
                    }
                }
                }
        url = "https://tourplanning.hereapi.com/v3/problems"
        autorization = "Bearer " + token
        print(autorization)
        headers = {
            "Authorization": autorization,
            "Content-Type": "application/json"
        }

        # Print the response
        response = post(url, json=body, headers=headers)

        print(response.status_code)
        print(response.json())
        #for mo in self.mission_order_ids:

        # mo_len = len(self.mission_order_ids) - 1
        # origin = ""
        # waypoints = ""
        # destination = ""
        # i = 0
        # if mo_len == 0:
        #         origin = str(self.mission_order_ids[i].loading.latitude) + "," + str(self.mission_order_ids[i].loading.longitude)
        #         destination = str(self.mission_order_ids[i].delivery.latitude) + "," + str(self.mission_order_ids[i].delivery.longitude)
        # else:
        #     while i <= mo_len:
        #         if not origin:
        #             origin = str(self.mission_order_ids[i].loading.latitude) + "," + str(self.mission_order_ids[i].loading.longitude)
        #             waypoints += str(self.mission_order_ids[i].delivery.latitude) + "," + str(self.mission_order_ids[i].delivery.longitude)
        #         elif origin and i != mo_len:
        #             if self.mission_order_ids[i-1].delivery.full_address == self.mission_order_ids[i].loading.full_address:
        #                 waypoints +=  "&via=" + str(self.mission_order_ids[i].delivery.latitude) + "," + str(self.mission_order_ids[i].delivery.longitude)
        #             else:
        #                 waypoints += "&via=" + str(self.mission_order_ids[i].loading.latitude) + "," + str(self.mission_order_ids[i].loading.longitude) + "&via=" + str(self.mission_order_ids[i].delivery.latitude) + "," + str(self.mission_order_ids[i].delivery.longitude)
        #         elif origin and i == mo_len:
        #             if self.mission_order_ids[i-1].delivery.full_address == self.mission_order_ids[i].loading.full_address:
        #                 pass
        #             else:
        #                 waypoints += "&via=" + str(self.mission_order_ids[i].loading.latitude) + "," + str(self.mission_order_ids[i].loading.longitude)
        #             destination = str(self.mission_order_ids[i].delivery.latitude) + "," + str(self.mission_order_ids[i].delivery.longitude)
        #         i+=1
        # if waypoints:
        #     request = "https://router.hereapi.com/v8/routes?apikey=%s&origin=%s&destination=%s&via=%s&return=summary,tolls&transportMode=truck&currency=EUR&truck[grossWeight]=12000&truck[height]=400" % (here_api_key, origin, destination, waypoints)
        # else:
        #     request = "https://router.hereapi.com/v8/routes?apikey=%s&origin=%s&destination=%s&return=summary,tolls&transportMode=truck&currency=EUR&truck[grossWeight]=12000&truck[height]=400" % (here_api_key, origin, destination)
        # request_get = get(url = request)
        # requests_result = request_get.json()
        # driving_time = 0
        # distance_km = 0
        # toll_cost = 0
        # ferry_time = 0
        # includes_ferry = False
        # for section in requests_result['routes'][0]["sections"]:
        #     if section.get('tolls'):
        #         for toll in section["tolls"]:
        #             toll_cost += toll['fares'][0]['convertedPrice']['value']
        #     if section['transport']['mode'] in ['truck', 'carShuttleTrain']:
        #         driving_time += section['summary']["duration"] / 60 / 60
        #         distance_km += section['summary']["length"] / 1000
        #     if section['transport']['mode'] in ['ferry']:
        #         ferry_time += section['summary']["duration"] / 60 / 60
        #         includes_ferry = True
            
        # self.toll_cost = toll_cost
        # self.fuel_cost = float(distance_km) * float(truck_fuel_consumption) / 100 * float(fuel_cost)
        # self.total_cost = self.toll_cost + self.fuel_cost
        # self.distance = round(float(distance_km),2)
        # self.driving_time = float(driving_time)
        # self.ferry_time = float(ferry_time)
        # self.includes_ferry = includes_ferry

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