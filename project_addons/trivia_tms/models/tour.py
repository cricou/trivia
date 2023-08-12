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
from datetime import datetime

class TriviaTour(models.Model):
    _name = 'trivia.tour'
    _description = 'TRIVIA Tour'
    _inherit = ['mail.thread']

    name = fields.Char(string="Name", copy=False, readonly=True)
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    mission_order_ids = fields.Many2many('mission.order', string="Missions order")

    start_position = fields.Many2one('point.of.interest')
    end_position = fields.Many2one('point.of.interest')

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
            "oauth_version": "1.0"
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
            "grant_type": "client_credentials"
        }

        # Envoi de la requête POST
        response = post(url, data=body, headers=headers)
        if response.status_code == 200:
            token_json = response.json()
            return token_json["access_token"]

    def create_steps(self, json):
        statistic = json['statistic']
        tours = json['tours']
        sequence=1
        for tour in tours:
            for stop in tour['stops']:
                for activitie in stop['activities']:
                    vehicle_id = tour['typeId']
                    full_address = None
                    
                    mo_id=None
                    activity_type = activitie['type']
                    if activitie['type'] in ['pickup', 'delivery']:
                        mo_id = activitie.get('jobId') or None
                    elif activitie['type'] == 'departure':
                        full_address = self.start_position.full_address
                    elif activitie['type'] == 'arrival':
                        full_address = self.end_position.full_address
                    if activitie['time'].get('start'):
                        arrival_reformat = activitie['time']['start'].replace("Z","")
                        arrival_date = datetime.strptime(arrival_reformat, "%Y-%m-%dT%H:%M:%S")
                    else:
                        arrival_date = None
                    if activitie['time'].get('end'):
                        departure_reformat = activitie['time']['end'].replace("Z","")
                        departure_date = datetime.strptime(departure_reformat, "%Y-%m-%dT%H:%M:%S")
                    else:
                        departure_date = None
                    if len(stop["load"]) == 1:
                        reserved_payload = stop["load"][0]
                        reserved_length = stop["load"][0]
                    else:
                        reserved_payload = stop["load"][1]
                        reserved_length = stop["load"][0]
                    if mo_id:
                        mo = self.env['mission.order'].search([('id', '=', mo_id)])
                        if activity_type == "pickup":
                            full_address = mo.loading.full_address
                        if activity_type == "delivery":
                            full_address = mo.delivery.full_address
                    self.env['trivia.tour.step'].create({
                        "sequence": sequence,
                        "tour_id": self.id,
                        "mission_order_id": mo_id,
                        "activity_type": activity_type,
                        "distance": float(stop['distance']) / 1000,
                        "arrival_date": arrival_date,
                        "departure_date": departure_date,
                        "reserved_payload": float(reserved_payload) / self.vehicle_id.semi_trailer_id.payload_capacity * 100,
                        "reserved_length": (float(reserved_length) / 100) / self.vehicle_id.semi_trailer_id.internal_length * 100,
                        "full_address": full_address,
                        "vehicle_id": vehicle_id
                    })
                    sequence += 1
                
    def tour_step_configuration(self):
        return False

    def tour_step_fleet(self):

        truck_fuel_consumption = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.truck_fuel_consumption')
    
        start_date = str(self.start_date.isoformat('T') + "Z")
        end_date = str(self.end_date.isoformat('T') + "Z")
        distance = float(truck_fuel_consumption) / 100000

        #capacity
        capacity_length = int(self.vehicle_id.semi_trailer_id.internal_length * 100)
        capacity_payload = int(self.vehicle_id.semi_trailer_id.payload_capacity)
        capacity = [capacity_length, capacity_payload]
        fleet = {}
        types = [
            {
                "id": str(self.vehicle_id.id),
                "profile": self.vehicle_id.model_id.name,
                "costs": {
                    "fixed": 0,
                    "distance": distance,
                    "time": 0
                },
                "shifts": [
                    {
                        "start": {
                            "time": start_date,
                            "location": {
                                "lat": self.start_position.latitude,
                                "lng": self.start_position.longitude
                            },
                            "timeOffset": 7200
                        }
                    }
                ],
                "capacity": capacity,
                "limits": {
                    "shiftTime": 36000
                },
                "amount": 1
            }
        ]

        profiles = [
            {
            "type": self.vehicle_id.model_id.vehicle_type,
            "name": self.vehicle_id.model_id.name
            }
        ]

        if self.end_position:
            types[0]['shifts'][0]['end'] = {
                                        "time": end_date,
                                        "location": {
                                            "lat": self.end_position.latitude,
                                            "lng": self.end_position.longitude
                                        },
                                        "timeOffset": 7200
                                    }
        fleet['types'] = types
        fleet['profiles'] = profiles

        return fleet

    def tour_step_plan(self):
        start_date = str(self.start_date.isoformat('T') + "Z")
        end_date = str(self.end_date.isoformat('T') + "Z")
        plan = {}
        jobs = []
        for mo in self.mission_order_ids:
            cargo_length = int(mo.cargo_length * 100)
            cargo_payload = int(mo.cargo_payload)
            demand = [cargo_length, cargo_payload]
            job = {
                "id": str(mo.id),
                "tasks": {
                    "pickups": [
                        {
                            "places": [
                            {
                                "times": [
                                    [
                                        start_date,
                                        end_date
                                    ]
                                ],
                                "location": {
                                    "lat": mo.loading.latitude,
                                    "lng": mo.loading.longitude
                                },
                                "duration": 900,
                                "tag": str(mo.id)
                            }
                            ],
                            "demand": demand
                        }
                    ],
                    "deliveries": [
                        {
                            "places": [
                                {
                                    "times": [
                                        [
                                            start_date,
                                            end_date
                                        ]
                                    ],
                                    "location": {
                                        "lat": mo.delivery.latitude,
                                        "lng": mo.delivery.longitude
                                    },
                                    "duration": 900
                                }
                            ],
                            "demand": demand
                        }
                    ]
                }
            }
            jobs.append(job)
            plan['jobs'] = jobs
        return plan

    def tour_step_objectives(self):
        return False   

    def calc_tour_step(self):
        # self.create_steps(json={'statistic': {'cost': 121.57887500000001, 'distance': 381125, 'duration': 28699, 'times': {'driving': 21499, 'serving': 7200, 'waiting': 0, 'stopping': 0, 'break': 0}}, 'tours': [{'vehicleId': '1_1', 'typeId': '1', 'stops': [{'location': {'lat': 45.707, 'lng': 4.85531}, 'time': {'arrival': '2023-08-16T06:00:00Z', 'departure': '2023-08-16T06:00:00Z'}, 'load': [0], 'activities': [{'jobId': 'departure', 'type': 'departure', 'location': {'lat': 45.707, 'lng': 4.85531}, 'time': {'start': '2023-08-16T06:00:00Z', 'end': '2023-08-16T06:00:00Z'}}], 'distance': 0}, {'location': {'lat': 45.75917, 'lng': 4.82965}, 'time': {'arrival': '2023-08-16T06:25:30Z', 'departure': '2023-08-16T06:40:30Z'}, 'load': [600, 15000], 'activities': [{'jobId': '16', 'type': 'pickup', 'jobTag': '16', 'location': {'lat': 45.75917, 'lng': 4.82965}, 'time': {'start': '2023-08-16T06:25:30Z', 'end': '2023-08-16T06:40:30Z'}}], 'distance': 13000}, {'location': {'lat': 45.77077, 'lng': 4.9587}, 'time': {'arrival': '2023-08-16T07:13:18Z', 'departure': '2023-08-16T07:28:18Z'}, 'load': [900, 17000], 'activities': [{'jobId': '5', 'type': 'pickup', 'jobTag': '5', 'location': {'lat': 45.77077, 'lng': 4.9587}, 'time': {'start': '2023-08-16T07:13:18Z', 'end': '2023-08-16T07:28:18Z'}}], 'distance': 36999}, {'location': {'lat': 45.662, 'lng': 5.08079}, 'time': {'arrival': '2023-08-16T07:57:18Z', 'departure': '2023-08-16T08:12:18Z'}, 'load': [1100, 23000], 'activities': [{'jobId': '11', 'type': 'pickup', 'jobTag': '11', 'location': {'lat': 45.662, 'lng': 5.08079}, 'time': {'start': '2023-08-16T07:57:18Z', 'end': '2023-08-16T08:12:18Z'}}], 'distance': 59013}, {'location': {'lat': 45.66291, 'lng': 4.95721}, 'time': {'arrival': '2023-08-16T08:36:05Z', 'departure': '2023-08-16T08:51:05Z'}, 'load': [900, 17000], 'activities': [{'jobId': '11', 'type': 'delivery', 'location': {'lat': 45.66291, 'lng': 4.95721}, 'time': {'start': '2023-08-16T08:36:05Z', 'end': '2023-08-16T08:51:05Z'}}], 'distance': 73656}, {'location': {'lat': 44.93045, 'lng': 4.88924}, 'time': {'arrival': '2023-08-16T10:14:54Z', 'departure': '2023-08-16T10:29:54Z'}, 'load': [600, 15000], 'activities': [{'jobId': '5', 'type': 'delivery', 'location': {'lat': 44.93045, 'lng': 4.88924}, 'time': {'start': '2023-08-16T10:14:54Z', 'end': '2023-08-16T10:29:54Z'}}], 'distance': 173798}, {'location': {'lat': 43.96189, 'lng': 4.85993}, 'time': {'arrival': '2023-08-16T12:04:38Z', 'departure': '2023-08-16T12:34:38Z'}, 'load': [900, 17000], 'activities': [{'jobId': '16', 'type': 'delivery', 'location': {'lat': 43.96189, 'lng': 4.85993}, 'time': {'start': '2023-08-16T12:04:38Z', 'end': '2023-08-16T12:19:38Z'}}, {'jobId': '6', 'type': 'pickup', 'jobTag': '6', 'location': {'lat': 43.96189, 'lng': 4.85993}, 'time': {'start': '2023-08-16T12:19:38Z', 'end': '2023-08-16T12:34:38Z'}}], 'distance': 297260}, {'location': {'lat': 43.52638, 'lng': 5.44614}, 'time': {'arrival': '2023-08-16T13:43:19Z', 'departure': '2023-08-16T13:58:19Z'}, 'load': [0, 0], 'activities': [{'jobId': '6', 'type': 'delivery', 'location': {'lat': 43.52638, 'lng': 5.44614}, 'time': {'start': '2023-08-16T13:43:19Z', 'end': '2023-08-16T13:58:19Z'}}], 'distance': 381125}], 'statistic': {'cost': 121.57887500000001, 'distance': 381125, 'duration': 28699, 'times': {'driving': 21499, 'serving': 7200, 'waiting': 0, 'stopping': 0, 'break': 0}}, 'shiftIndex': 0}]})
        # return
        token = self.getAuthToken()
        body = {}

        configuration = self.tour_step_configuration()
        fleet = self.tour_step_fleet()
        plan = self.tour_step_plan()
        objectives = self.tour_step_objectives()

        if plan:
            body["plan"] = plan
        if fleet:
            body["fleet"] = fleet
        if objectives:
            body["objectives"] = objectives
        if configuration:
            body["configuration"] = configuration
        print(body)
        url = "https://tourplanning.hereapi.com/v3/problems"
        autorization = "Bearer " + token
        print(autorization)
        headers = {
            "Authorization": autorization,
            "Content-Type": "application/json"
        }

        response = post(url, json=body, headers=headers)
        if response.status_code == 200:
            self.create_steps(json=response.json())
        print(response.status_code)
        print(response.json()) 

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