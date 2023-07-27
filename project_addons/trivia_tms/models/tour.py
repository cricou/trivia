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

    name = fields.Char(string="Name",
                       default=lambda self: self.env['ir.sequence'].next_by_code('trivia_tms.tour'))
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    mission_order_ids = fields.Many2many('mission.order', string="Missions order")

    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    driver_id = fields.Many2one('res.partner', related='vehicle_id.driver_id')
    
    driving_time = fields.Float(string="Driving time", compute='_calc_driving_time')
    distance = fields.Float(string="Distance", compute='_calc_distance')
    fuel_cost = fields.Float(string="Fuel cost", compute='_calc_fuel_cost')
    toll_cost = fields.Float(string="Tolls cost", compute='_calc_toll_cost')
    total_cost = fields.Float(string="Total cost", compute='_calc_total_cost')

    @api.depends('mission_order_ids')
    def _calc_distance(self):
        for record in self:
            result = 0
            for rec in self.mission_order_ids:
                result += rec.distance
            record.distance = result

    @api.depends('mission_order_ids')
    def _calc_driving_time(self):
        for record in self:
            result = 0
            for rec in self.mission_order_ids:
                result += rec.driving_time
            record.driving_time = result
    
    @api.depends('mission_order_ids')
    def _calc_fuel_cost(self):
        for record in self:
            result = 0
            for rec in self.mission_order_ids:
                result += rec.fuel_cost
            record.fuel_cost = result

    @api.depends('mission_order_ids')
    def _calc_toll_cost(self):
        for record in self:
            result = 0
            for rec in self.mission_order_ids:
                result += rec.toll_cost
            record.toll_cost = result
    
    @api.depends('mission_order_ids')
    def _calc_total_cost(self):
        for record in self:
            result = 0
            for rec in self.mission_order_ids:
                result += rec.total_cost
            record.total_cost = result

    def google_map_url(self):
        if self.id:
            
            mo_len = len(self.mission_order_ids) - 1
            print(mo_len)
            origin = ""
            waypoints = ""
            destination = ""
            i = 0
            for rec in self.mission_order_ids:
                print(rec)
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
            print(google_map_url)
           
            return {
                'type': 'ir.actions.act_url',
                'url': google_map_url,
                'target': 'new',
            }