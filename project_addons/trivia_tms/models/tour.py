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
import os

class TriviaTour(models.Model):
    _name = 'trivia.tour'
    _description = 'TRIVIA Tour'
    _inherit = ['mail.thread']

    sequence = fields.Integer()
    name = fields.Char(string="Name", copy=False, readonly=True)
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    start_position = fields.Many2one('point.of.interest')
    end_position = fields.Many2one('point.of.interest')

    note = fields.Text(string="Note")

    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    driver_id = fields.Many2one('res.partner', related='vehicle_id.driver_id')
    
    driving_time = fields.Float(string="Driving time")
    distance = fields.Float(string="Distance")
    duration = fields.Float(string="Duration")
    fuel_cost = fields.Float(string="Fuel cost")
    toll_cost = fields.Float(string="Tolls cost")
    total_cost = fields.Float(string="Total cost")

    tour_step_ids = fields.One2many('trivia.tour.step', 'tour_id', string="Tour Steps")
    tour_plan_id = fields.Many2one('trivia.tour.plan')

    mission_order_ids = fields.Many2many('mission.order', string="Missions order")

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