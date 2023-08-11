# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from requests import get, post, HTTPError
import json
from json import dumps
import http.client
import time
from datetime import datetime

MO_STATUS=[
    ('draft', "Draft"),
    ('in_progress', "In progress"),
    ('done', "Done")
]

class MissionOrder(models.Model):
    _name = 'mission.order'
    _description = 'Mission Order'
    _inherit = ['mail.thread']
    _order = 'sequence'

    sequence = fields.Integer(string="Sequence")
    name = fields.Char(string="Name", copy=False, readonly=True)
    date = fields.Date(string="Order date",
                       default=lambda self: fields.Date.today())
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
    includes_ferry = fields.Boolean(string = "Includes Ferry")
    ferry_time = fields.Float(string="Ferry time")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    driver_id = fields.Many2one('res.partner')
    semi_trailer_id = fields.Many2one('trivia.semi.trailer', string="Semi Trailer")
    fixed_price = fields.Float(string="Fixed Price")
    price_per_km = fields.Float(string="Price/Km", compute='_calc_price_km')
    account_move_id = fields.Many2one('account.move', string="Invoice")

    #loading
    cargo_length = fields.Float(string="Cargo Length")
    cargo_payload = fields.Float(string="Cargo Payload")

    reserved_length = fields.Float(string="Reserved Length", compute='_calc_reserved_length')
    reserved_payload = fields.Float(string="Reserved Payload", compute='_calc_reserved_payload')

    partner_id = fields.Many2one('res.partner')

    @api.model
    def create(self, values):
        if not values.get('name'):
            # fallback on any pos.order sequence
            values['name'] = self.env['ir.sequence'].next_by_code('trivia_tms.mission.order')
        return super(MissionOrder, self).create(values)

    def action_create_invoice(self):
        if not self.partner_id:
            raise ValidationError("You must add a partner to create an invoice")
        line = {
            'name': self.loading.full_address + " - " + self.delivery.full_address,
            'price_unit': self.fixed_price,
            'tax_ids': [(6, 0, [1])]
        }
        invoice_id = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'partner_shipping_id': self.partner_id.id,
            'payment_reference': self.name,
            'invoice_payment_term_id': self.partner_id.property_payment_term_id.id,
            'invoice_date': datetime.now(),
            'invoice_line_ids': [
                (0, 0, line),
            ],
        })
        print(invoice_id)
        self.account_move_id = invoice_id

    def _calc_reserved_payload(self):
        for rec in self:
            print(rec)
            if rec.semi_trailer_id and rec.semi_trailer_id.payload_capacity != 0 and rec.cargo_payload != 0:
                rec.reserved_payload = rec.cargo_payload / rec.semi_trailer_id.payload_capacity * 100
            else:
                rec.reserved_payload = None
            
    def _calc_reserved_length(self):
        for rec in self:
            if rec.semi_trailer_id and rec.semi_trailer_id.internal_length != 0 and rec.cargo_length != 0:
                rec.reserved_length = rec.cargo_length / rec.semi_trailer_id.internal_length * 100
            else:
                rec.reserved_length = None

    def _calc_price_km(self):
        for rec in self:
            if rec.fixed_price and rec.distance:
                rec.price_per_km = rec.fixed_price / rec.distance
            else:
                rec.price_per_km = 0

    @api.onchange('vehicle_id')
    def get_driver(self):
        if self.vehicle_id:
            self.driver_id = self.vehicle_id.driver_id
            self.semi_trailer_id = self.vehicle_id.semi_trailer_id
        else:
            self.driver_id = None
            self.semi_trailer_id = None


    def calc_routes(self):
        here_api_key = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.here_api_key')
        truck_fuel_consumption = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.truck_fuel_consumption')
        fuel_cost = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.fuel_cost')

        origin_coordinate = str(self.loading.latitude) + "," + str(self.loading.longitude)
        destination_coordinate = str(self.delivery.latitude) + "," + str(self.delivery.longitude)
        
        request = "https://router.hereapi.com/v8/routes?apikey=%s&origin=%s&destination=%s&return=summary,tolls&transportMode=truck&currency=EUR&truck[grossWeight]=12000&truck[height]=400" % (here_api_key, origin_coordinate, destination_coordinate)
        request_get = get(url = request)
        requests_result = request_get.json()
        driving_time = 0
        distance_km = 0
        toll_cost = 0
        ferry_time = 0
        includes_ferry = False
        sections = requests_result['routes'][0]['sections']
        for section in sections:
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

