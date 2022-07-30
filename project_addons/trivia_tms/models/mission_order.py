# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from requests import get, post, HTTPError
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

    name = fields.Char(string="Name")
    date = fields.Date(string="Order date")
    main_carrier = fields.Many2one('res.partner', string="Main carrier")
    substitued_carrier = fields.Many2one('res.partner', string="Substitued carrier")
    driver = fields.Many2one('res.partner', string="Driver")
    loading = fields.Many2one('res.partner', string="Loading")
    loading_date = fields.Datetime(string="Loading date")
    delivery = fields.Many2one('res.partner', string="Delivery")
    delivery_date = fields.Datetime(string="Delivery date")
    note = fields.Text(string="Note")
    state = fields.Selection(selection=MO_STATUS, default="draft")
    #Route
    driving_time = fields.Float(string="Driving time")
    distance = fields.Float(string="Distance")
    fuel_cost = fields.Float(string="Fuel cost")
    toll_cost = fields.Float(string="Tolls cost")
    total_cost = fields.Float(string="Total cost")


