# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.trivia_tms.tutils import Tutils
from requests import get, post, HTTPError, utils
import http.client
import json
from json import dumps

STATE=[
    ('draft', "Draft"),
    ('in_progress', "In progress"),
    ('calculated', "Calculated")
]

class TriviaTourPlan(models.Model):
    _name = 'trivia.tour.plan'
    _description = 'TRIVIA Tour plan'
    _inherit = ['mail.thread']

    name = fields.Char(string="Name", copy=False, readonly=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    mission_order_ids = fields.Many2many('mission.order', string="Missions order")
    tour_plan_fleet_ids = fields.One2many('trivia.tour.plan.fleet', 'tour_plan_id')
    
    note = fields.Text(string="Note")

    tour_ids = fields.One2many('trivia.tour', 'tour_plan_id')
    tour_count = fields.Integer(compute='_calc_tour_count')
    state = fields.Selection(selection=STATE, default='draft')

    @api.onchange('start_date', 'end_date')
    def _compute_mission_order_domain(self):
        self.mission_order_ids = None
        domain = {'mission_order_ids': []}
        for rec in self:
            if rec.start_date and rec.end_date:
                start_date = rec.start_date
                end_date = rec.end_date
                domain = {'mission_order_ids': [
                    ('state', 'in', ['draft', 'in_progress']),
                    '|', '|', '|',
                    '&', ('loading_start_date', '>=', start_date), ('loading_start_date', '<=', end_date),
                    '&', ('loading_end_date', '>=', start_date), ('loading_end_date', '<=', end_date),
                    '&', ('delivery_start_date', '>=', start_date), ('delivery_start_date', '<=', end_date),
                    '&', ('delivery_end_date', '>=', start_date), ('delivery_end_date', '<=', end_date)
                ]}
        return {'domain': domain}

    @api.model
    def create(self, values):
        if not values.get('name'):
            # fallback on any pos.order sequence
            values['name'] = self.env['ir.sequence'].next_by_code('trivia_tms.tour_plan')
        return super(TriviaTourPlan, self).create(values)

    def _calc_tour_count(self):
        self.ensure_one()
        for rec in self:
            rec.tour_count = len(rec.tour_ids)

    def open_tour(self):
        return {
            'name': 'Tour',
            'domain': [('tour_plan_id', '=', self.id)],
            'res_model': 'trivia.tour',
            'target': 'current',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }
    
    def tour_step_configuration(self):
        return False
    
    def tour_step_fleet_types(self, fleet):
        v_type = fleet.tour_vehicle_type_id
        profile = fleet.tour_vehicle_type_id.tour_profile_id
        shift_time = Tutils.convert_float_time_to_second(fleet.shift_time)
        break_duration = Tutils.convert_float_time_to_second(fleet.break_duration)
        try:
            capacity = eval(v_type.capacity)
        except:
            capacity = [1]

        type_obj = {
                "id": "%s-%s" % (v_type.id,fleet.is_external_fleet),
                "profile": profile.name,
                "costs": {
                    "fixed": v_type.fixed_cost,
                    "distance": v_type.distance_cost,
                    "time": v_type.time_cost
                },
                "capacity": capacity,
                "limits": {
                    "shiftTime": shift_time
                },
            }

        if fleet.is_external_fleet:
            type_obj['amount'] = fleet.vehicle_amount
        else:
            vehicles = []
            for vehicle in fleet.vehicle_ids:
                vehicles.append("fleet_vehicle-%s" % vehicle.id)
            type_obj['vehicleIds'] = vehicles
        if v_type.tour_skill_ids:
            skills = []
            for skill in v_type.tour_skill_ids:
                skills.append(skill.name)
            type_obj['skills'] = skills

        #TODO ADD BREAK
        # breaks = []
        
        # shift_break = {
        #     "duration": break_duration,
        #     "times":[

        #     ]
        # }

        shifts = []
        for shift in fleet.tour_plan_fleet_shift_ids:
            obj = {
                "start": {
                    "time": Tutils.convert_datetime_to_isoformat(shift.start_date),
                    "location": {
                        "lat": shift.shift_location_start.latitude,
                        "lng": shift.shift_location_start.longitude
                    },
                    "timeOffset": Tutils.convert_float_time_to_second(shift.shift_offset_start) or 0
                },
                
            }
            if shift.end_date and shift.shift_location_end:
                obj['end'] = {
                    "time": Tutils.convert_datetime_to_isoformat(shift.end_date),
                    "location": {
                        "lat": shift.shift_location_end.latitude,
                        "lng": shift.shift_location_end.longitude
                    }
                }
            shifts.append(obj)
        type_obj["shifts"] = shifts
        profile_obj = {
            "type": profile.profile_type,
            "name": profile.name
        }
        result = {
            "type": type_obj,
            "profile": profile_obj
        }
        return result


    def tour_step_fleet(self):
        fleet_result = {}
        types = []
        profiles = []
        
        for fleet in self.tour_plan_fleet_ids:
            result = self.tour_step_fleet_types(fleet)
            types.append(result['type'])
            profiles.append(result['profile'])

        fleet_result['types'] = types
        fleet_result['profiles'] = profiles

        return fleet_result

    def tour_step_plan_jobs(self, mo):
        cargo_length = int(mo.cargo_length)
        cargo_payload = int(mo.cargo_payload)
        demand = [cargo_length, cargo_payload]
        loading_start_date = Tutils.convert_datetime_to_isoformat(mo.loading_start_date)
        loading_end_date = Tutils.convert_datetime_to_isoformat(mo.loading_end_date)
        delivery_end_date = Tutils.convert_datetime_to_isoformat(mo.delivery_end_date)
        delivery_start_date = Tutils.convert_datetime_to_isoformat(mo.delivery_start_date)

        job = {
                "id": str("mission_order-%s" % mo.id),
                "tasks": {
                    "pickups": [
                        {
                            "places": [
                            {
                                "times": [
                                    [
                                        loading_start_date,
                                        loading_end_date
                                    ]
                                ],
                                "location": {
                                    "lat": mo.loading.latitude,
                                    "lng": mo.loading.longitude
                                },
                                "duration": 60,
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
                                            delivery_start_date,
                                            delivery_end_date
                                        ]
                                    ],
                                    "location": {
                                        "lat": mo.delivery.latitude,
                                        "lng": mo.delivery.longitude
                                    },
                                    "duration": 60,
                                    "tag": str(mo.id)
                                }
                            ],
                            "demand": demand
                        }
                    ]
                }
            }
        return job


    def tour_step_plan(self):
        plan_result = {}
        jobs = []
        for mo in self.mission_order_ids:
            result = self.tour_step_plan_jobs(mo)
            jobs.append(result)
        plan_result['jobs'] = jobs

        return plan_result

    def tour_step_objectives(self):
        return False

    def action_calc_tour_plan(self):
        body = {}
        token = Tutils.getHereAuthToken()
        print(token)
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

        headers = {
            "Authorization": autorization,
            "Content-Type": "application/json"
        }

        response = post(url, json=body, headers=headers)
        # if response.status_code == 200:
        #     print(response.json()) 
        print(response.status_code)
        print(response.json()) 
        