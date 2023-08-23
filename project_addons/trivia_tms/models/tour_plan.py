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
    unassigned_mo_ids = fields.Many2many(comodel_name='mission.order',
                                         relation="tour_plan_mo_un_rel",
                                         column1='tour_plan_id',
                                         column2='mo_id',
                                         string="Unassigned Missions Order",
                                         )
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
            'view_mode': 'tree,form,here_map',
            'type': 'ir.actions.act_window'
        }
    
    def tour_step_configuration(self):
        return False
    
    def tour_step_fleet_types(self, fleet):
        v_type = fleet.tour_vehicle_type_id
        profile = fleet.tour_vehicle_type_id.tour_profile_id
        shift_time = Tutils.convert_float_time_to_second(fleet.shift_time)

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
            if shift.break_start_date and shift.break_end_date and shift.break_duration != 0:
                obj['breaks'] = [
                    {
                        'duration': Tutils.convert_float_time_to_second(shift.break_duration),
                        'times':[
                            [
                                Tutils.convert_datetime_to_isoformat(shift.break_start_date),
                                Tutils.convert_datetime_to_isoformat(shift.break_end_date)
                            ]
                        ]
                    }
                ]
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

    def get_tours_statistic(self, json):
        #TODO Statistic
        return

    def get_tour_info(self,tour):
        vehicle_type_model = self.env['trivia.tour.vehicle.type']
        fleet_vehicle_model = self.env['fleet.vehicle']
        vehicle_type = tour["typeId"].split('-')
        vehicle_type_id = int(vehicle_type[0])
        vehicle_type_obj = vehicle_type_model.search([('id', '=', vehicle_type_id)])
        vehicle_type_name = vehicle_type_obj.name
        is_ext_fleet = False if vehicle_type[1] == "False" else True
        tour_name = None
        vehicle_obj = None
        tour_plan_fleet_obj = self.env['trivia.tour.plan.fleet'].search(
                [
                    ('is_external_fleet', '=', is_ext_fleet),
                    ('tour_vehicle_type_id', '=', vehicle_type_id),
                    ('tour_plan_id', '=', self.id)
                ],
                limit=1
            )
        
        if is_ext_fleet:
            vehicle_num = tour["vehicleId"].split('_')[1]
            tour_name = "%s - Vehicle %s" % (vehicle_type_name, vehicle_num)
        else:
            vehicle_obj = fleet_vehicle_model.search([('id', '=', int(tour["vehicleId"].split('-')[1]))])
            tour_name = "%s - %s" % (vehicle_type_name, vehicle_obj.name)
        
        result = {
            'is_ext_fleet': is_ext_fleet,
            'tour_name': tour_name,
            'vehicle_obj': vehicle_obj,
            'vehicle_type_obj': vehicle_type_obj,
            'tour_plan_fleet_obj': tour_plan_fleet_obj
        }
        return result

    def get_activities_info(self, activities):
        result = {}
        activity_values = []
        activity_type_list = []
        activity_type_model = self.env['trivia.tour.step.activity.type']
        
        for activity in activities:
            mission_order_id = activity.get('jobTag') if activity.get('jobTag') else None
            arrival_date = Tutils.convert_isoformat_to_datetime(activity['time']['start'])
            departure_date = Tutils.convert_isoformat_to_datetime(activity['time']['end'])
            activity_type = activity['type']
            activity_type_id = activity_type_model.search([('ref', '=', activity_type)])
            activity_type_list.append(activity_type_id)
            activity_values.append(
                {
                    'mission_order_id': mission_order_id,
                    'arrival_date': arrival_date,
                    'departure_date': departure_date,
                    'activity_type_id': activity_type_id.id if activity_type_id else None
                }
            )
        activity_type_ids = [(4, values.id) for values in set(activity_type_list)]
        print(activity_type_ids)
        activity_ids = [(0, 0, values) for values in activity_values]
        print(activity_ids)
        result['activity_type_ids'] = activity_type_ids
        result['activity_ids'] = activity_ids
        return result

            


    def get_steps_info(self, steps):
        mo_model = self.env['mission.order']
        poi_model = self.env['point.of.interest']
        step_values = []
        for step in steps:
            poi_obj = poi_model.search(
                    [
                        ('longitude', '=', step['location']['lng']),
                        ('latitude', '=', step['location']['lat'])
                    ],
                    limit=1
                )
            arrival_date = Tutils.convert_isoformat_to_datetime(step['time']['arrival'])
            departure_date = Tutils.convert_isoformat_to_datetime(step['time']['departure'])
            distance = Tutils.convert_meter_to_kilometer(step['distance'])
            load = str(step['load'])
            step_location = poi_obj.id if poi_obj else None
            activities_result = self.get_activities_info(step['activities'])

            step_values.append(
                {
                    'location_id': step_location,
                    'distance': distance,
                    'arrival_date': arrival_date,
                    'load': load,
                    'departure_date': departure_date,
                    'tour_step_activity_ids': activities_result['activity_ids'],
                    'tour_step_activity_type_ids': activities_result['activity_type_ids']
                }
            )

        tour_step_ids = [(0, 0, values) for values in step_values]
        return tour_step_ids


    def generate_tours(self, json):
        
        tour_model = self.env['trivia.tour']
        tours = json['tours']
        for tour in tours:

            # tour information
            statistic = tour['statistic']
            self.get_tours_statistic(statistic)
            first_step = tour['stops'][0]
            last_step = tour['stops'][-1]
            tour_info = self.get_tour_info(tour)
            shift_index = tour['shiftIndex']
            shift_obj = tour_info['tour_plan_fleet_obj'].tour_plan_fleet_shift_ids[shift_index]
            tour_start_date = Tutils.convert_isoformat_to_datetime(first_step['time']['departure'])
            tour_end_date = Tutils.convert_isoformat_to_datetime(last_step['time']['departure'])

            #steps informations
            steps_ids = self.get_steps_info(tour['stops'])

                

            tour_model.create(
                {
                    'name': tour_info['tour_name'],
                    'tour_plan_id': self.id,
                    'start_date': tour_start_date,
                    'end_date': tour_end_date,
                    'vehicle_id': tour_info['vehicle_obj'].id if tour_info.get('vehicle_obj') else None,
                    'start_position': shift_obj.shift_location_start.id if shift_obj.shift_location_start else None,
                    'end_position': shift_obj.shift_location_end.id if shift_obj.shift_location_end else None,
                    'driving_time': Tutils.convert_second_to_float_time(statistic['times']['driving']),
                    'distance': Tutils.convert_meter_to_kilometer(statistic['distance']),
                    'duration': Tutils.convert_second_to_float_time(statistic['duration']),
                    'tour_step_ids': steps_ids
                }
            )



    def _get_tour_polylines(self, json):
        polylines = []
        for route in json['routes']:
            for section in route['sections']:
                if section.get('polyline'):
                    polylines.append(section['polyline'])
        return polylines


    def _calc_tour_route(self):
        here_api_key = self.env['ir.config_parameter'].sudo().get_param('trivia_tms.here_api_key')
        for tour in self.tour_ids:
            waypoints = []
            origine_coord =  "%s,%s" % (tour.start_position.latitude,tour.start_position.longitude)
            if tour.end_position:
                destination_coord = "%s,%s" % (tour.end_position.latitude,tour.end_position.longitude)
            else:
                destination_coord = "%s,%s" % (tour.tour_step_ids[-1].location_id.latitude,tour.tour_step_ids[-1].location_id.longitude,)
            if len(tour.tour_step_ids) > 2:
                for step in tour.tour_step_ids:
                    waypoints.append(
                        "%s,%s" % (step.location_id.latitude, step.location_id.longitude)
                    )
            tour.here_checkpoints = str(waypoints)
            waypoints = waypoints[1:-1]
            if waypoints:
                waypoints_str = "&".join([f"via={value}" for value in waypoints])
                request = "https://router.hereapi.com/v8/routes?apikey=%s&origin=%s&destination=%s&%s&return=polyline,summary,tolls&transportMode=truck&currency=EUR&truck[grossWeight]=12000&truck[height]=400" % (here_api_key, origine_coord, destination_coord, waypoints_str)
            else:
                request = "https://router.hereapi.com/v8/routes?apikey=%s&origin=%s&destination=%s&return=polyline,summary,tolls&transportMode=truck&currency=EUR&truck[grossWeight]=12000&truck[height]=400" % (here_api_key, origine_coord, destination_coord)
            request_get = get(url = request)
            requests_result = request_get.json()
            polylines_list = self._get_tour_polylines(requests_result)
            tour.here_polylines = str(polylines_list)

    def action_calc_tour_plan(self):
        # self.generate_tours({'statistic': {'cost': 158.70112, 'distance': 358441, 'duration': 41028, 'times': {'driving': 34908, 'serving': 2520, 'waiting': 0, 'stopping': 0, 'break': 3600}}, 'tours': [{'vehicleId': '1-True_1', 'typeId': '1-True', 'stops': [{'location': {'lat': 45.66291, 'lng': 4.95721}, 'time': {'arrival': '2023-08-29T03:00:00Z', 'departure': '2023-08-29T05:30:27Z'}, 'load': [0], 'activities': [{'jobId': 'departure', 'type': 'departure', 'location': {'lat': 45.66291, 'lng': 4.95721}, 'time': {'start': '2023-08-29T03:00:00Z', 'end': '2023-08-29T05:30:27Z'}}], 'distance': 0}, {'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'arrival': '2023-08-29T06:00:00Z', 'departure': '2023-08-29T06:02:00Z'}, 'load': [20, 2000], 'activities': [{'jobId': 'mission_order-435', 'type': 'pickup', 'jobTag': '435', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-29T06:00:00Z', 'end': '2023-08-29T06:01:00Z'}}, {'jobId': 'mission_order-436', 'type': 'pickup', 'jobTag': '436', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-29T06:01:00Z', 'end': '2023-08-29T06:02:00Z'}}], 'distance': 19641}, {'location': {'lat': 45.725041, 'lng': 4.786103}, 'time': {'arrival': '2023-08-29T06:33:41Z', 'departure': '2023-08-29T06:34:41Z'}, 'load': [10, 1000], 'activities': [{'jobId': 'mission_order-436', 'type': 'delivery', 'jobTag': '436', 'location': {'lat': 45.725041, 'lng': 4.786103}, 'time': {'start': '2023-08-29T06:33:41Z', 'end': '2023-08-29T06:34:41Z'}}], 'distance': 31944}, {'location': {'lat': 45.703908, 'lng': 4.64038}, 'time': {'arrival': '2023-08-29T07:15:31Z', 'departure': '2023-08-29T07:16:31Z'}, 'load': [0, 0], 'activities': [{'jobId': 'mission_order-435', 'type': 'delivery', 'jobTag': '435', 'location': {'lat': 45.703908, 'lng': 4.64038}, 'time': {'start': '2023-08-29T07:15:31Z', 'end': '2023-08-29T07:16:31Z'}}], 'distance': 53172}, {'location': {'lat': 45.66291, 'lng': 4.95721}, 'time': {'arrival': '2023-08-29T08:10:34Z', 'departure': '2023-08-29T08:10:34Z'}, 'load': [0, 0], 'activities': [{'jobId': 'arrival', 'type': 'arrival', 'location': {'lat': 45.66291, 'lng': 4.95721}, 'time': {'start': '2023-08-29T08:10:34Z', 'end': '2023-08-29T08:10:34Z'}}], 'distance': 91252}], 'statistic': {'cost': 51.20064000000001, 'distance': 91252, 'duration': 9607, 'times': {'driving': 9367, 'serving': 240, 'waiting': 0, 'stopping': 0, 'break': 0}}, 'shiftIndex': 1}, {'vehicleId': '1-True_1', 'typeId': '1-True', 'stops': [{'location': {'lat': 45.66291, 'lng': 4.95721}, 'time': {'arrival': '2023-08-28T03:00:00Z', 'departure': '2023-08-28T05:30:27Z'}, 'load': [0], 'activities': [{'jobId': 'departure', 'type': 'departure', 'location': {'lat': 45.66291, 'lng': 4.95721}, 'time': {'start': '2023-08-28T03:00:00Z', 'end': '2023-08-28T05:30:27Z'}}], 'distance': 0}, {'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'arrival': '2023-08-28T06:00:00Z', 'departure': '2023-08-28T06:16:00Z'}, 'load': [160, 16000], 'activities': [{'jobId': 'mission_order-421', 'type': 'pickup', 'jobTag': '421', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:00:00Z', 'end': '2023-08-28T06:01:00Z'}}, {'jobId': 'mission_order-407', 'type': 'pickup', 'jobTag': '407', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:01:00Z', 'end': '2023-08-28T06:02:00Z'}}, {'jobId': 'mission_order-440', 'type': 'pickup', 'jobTag': '440', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:02:00Z', 'end': '2023-08-28T06:03:00Z'}}, {'jobId': 'mission_order-380', 'type': 'pickup', 'jobTag': '380', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:03:00Z', 'end': '2023-08-28T06:04:00Z'}}, {'jobId': 'mission_order-439', 'type': 'pickup', 'jobTag': '439', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:04:00Z', 'end': '2023-08-28T06:05:00Z'}}, {'jobId': 'mission_order-437', 'type': 'pickup', 'jobTag': '437', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:05:00Z', 'end': '2023-08-28T06:06:00Z'}}, {'jobId': 'mission_order-415', 'type': 'pickup', 'jobTag': '415', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:06:00Z', 'end': '2023-08-28T06:07:00Z'}}, {'jobId': 'mission_order-427', 'type': 'pickup', 'jobTag': '427', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:07:00Z', 'end': '2023-08-28T06:08:00Z'}}, {'jobId': 'mission_order-384', 'type': 'pickup', 'jobTag': '384', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:08:00Z', 'end': '2023-08-28T06:09:00Z'}}, {'jobId': 'mission_order-412', 'type': 'pickup', 'jobTag': '412', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:09:00Z', 'end': '2023-08-28T06:10:00Z'}}, {'jobId': 'mission_order-364', 'type': 'pickup', 'jobTag': '364', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:10:00Z', 'end': '2023-08-28T06:11:00Z'}}, {'jobId': 'mission_order-379', 'type': 'pickup', 'jobTag': '379', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:11:00Z', 'end': '2023-08-28T06:12:00Z'}}, {'jobId': 'mission_order-419', 'type': 'pickup', 'jobTag': '419', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:12:00Z', 'end': '2023-08-28T06:13:00Z'}}, {'jobId': 'mission_order-403', 'type': 'pickup', 'jobTag': '403', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:13:00Z', 'end': '2023-08-28T06:14:00Z'}}, {'jobId': 'mission_order-383', 'type': 'pickup', 'jobTag': '383', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:14:00Z', 'end': '2023-08-28T06:15:00Z'}}, {'jobId': 'mission_order-361', 'type': 'pickup', 'jobTag': '361', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T06:15:00Z', 'end': '2023-08-28T06:16:00Z'}}], 'distance': 19641}, {'location': {'lat': 45.874552, 'lng': 4.712079}, 'time': {'arrival': '2023-08-28T06:53:21Z', 'departure': '2023-08-28T06:54:21Z'}, 'load': [150, 15000], 'activities': [{'jobId': 'mission_order-419', 'type': 'delivery', 'jobTag': '419', 'location': {'lat': 45.874552, 'lng': 4.712079}, 'time': {'start': '2023-08-28T06:53:21Z', 'end': '2023-08-28T06:54:21Z'}}], 'distance': 43641}, {'location': {'lat': 45.809106, 'lng': 4.568033}, 'time': {'arrival': '2023-08-28T07:24:03Z', 'departure': '2023-08-28T07:25:03Z'}, 'load': [140, 14000], 'activities': [{'jobId': 'mission_order-364', 'type': 'delivery', 'jobTag': '364', 'location': {'lat': 45.809106, 'lng': 4.568033}, 'time': {'start': '2023-08-28T07:24:03Z', 'end': '2023-08-28T07:25:03Z'}}], 'distance': 61295}, {'location': {'lat': 45.789178, 'lng': 4.537824}, 'time': {'arrival': '2023-08-28T07:37:12Z', 'departure': '2023-08-28T07:38:12Z'}, 'load': [130, 13000], 'activities': [{'jobId': 'mission_order-412', 'type': 'delivery', 'jobTag': '412', 'location': {'lat': 45.789178, 'lng': 4.537824}, 'time': {'start': '2023-08-28T07:37:12Z', 'end': '2023-08-28T07:38:12Z'}}], 'distance': 67000}, {'location': {'lat': 45.794457, 'lng': 4.531095}, 'time': {'arrival': '2023-08-28T07:44:57Z', 'departure': '2023-08-28T07:45:57Z'}, 'load': [120, 12000], 'activities': [{'jobId': 'mission_order-384', 'type': 'delivery', 'jobTag': '384', 'location': {'lat': 45.794457, 'lng': 4.531095}, 'time': {'start': '2023-08-28T07:44:57Z', 'end': '2023-08-28T07:45:57Z'}}], 'distance': 69299}, {'location': {'lat': 45.834028, 'lng': 4.522438}, 'time': {'arrival': '2023-08-28T07:59:59Z', 'departure': '2023-08-28T08:00:59Z'}, 'load': [110, 11000], 'activities': [{'jobId': 'mission_order-427', 'type': 'delivery', 'jobTag': '427', 'location': {'lat': 45.834028, 'lng': 4.522438}, 'time': {'start': '2023-08-28T07:59:59Z', 'end': '2023-08-28T08:00:59Z'}}], 'distance': 77984}, {'location': {'lat': 45.863209, 'lng': 4.550903}, 'time': {'arrival': '2023-08-28T08:13:40Z', 'departure': '2023-08-28T08:14:40Z'}, 'load': [100, 10000], 'activities': [{'jobId': 'mission_order-415', 'type': 'delivery', 'jobTag': '415', 'location': {'lat': 45.863209, 'lng': 4.550903}, 'time': {'start': '2023-08-28T08:13:40Z', 'end': '2023-08-28T08:14:40Z'}}], 'distance': 84253}, {'location': {'lat': 45.857308, 'lng': 4.643828}, 'time': {'arrival': '2023-08-28T08:30:27Z', 'departure': '2023-08-28T08:31:27Z'}, 'load': [90, 9000], 'activities': [{'jobId': 'mission_order-437', 'type': 'delivery', 'jobTag': '437', 'location': {'lat': 45.857308, 'lng': 4.643828}, 'time': {'start': '2023-08-28T08:30:27Z', 'end': '2023-08-28T08:31:27Z'}}], 'distance': 98750}, {'location': {'lat': 45.797201, 'lng': 4.620981}, 'time': {'arrival': '2023-08-28T08:46:29Z', 'departure': '2023-08-28T08:47:29Z'}, 'load': [80, 8000], 'activities': [{'jobId': 'mission_order-407', 'type': 'delivery', 'jobTag': '407', 'location': {'lat': 45.797201, 'lng': 4.620981}, 'time': {'start': '2023-08-28T08:46:29Z', 'end': '2023-08-28T08:47:29Z'}}], 'distance': 111227}, {'location': {'lat': 45.77713, 'lng': 4.588174}, 'time': {'arrival': '2023-08-28T09:00:10Z', 'departure': '2023-08-28T09:01:10Z'}, 'load': [70, 7000], 'activities': [{'jobId': 'mission_order-379', 'type': 'delivery', 'jobTag': '379', 'location': {'lat': 45.77713, 'lng': 4.588174}, 'time': {'start': '2023-08-28T09:00:10Z', 'end': '2023-08-28T09:01:10Z'}}], 'distance': 119321}, {'location': {'lat': 45.762144, 'lng': 4.492384}, 'time': {'arrival': '2023-08-28T09:17:16Z', 'departure': '2023-08-28T09:18:16Z'}, 'load': [60, 6000], 'activities': [{'jobId': 'mission_order-380', 'type': 'delivery', 'jobTag': '380', 'location': {'lat': 45.762144, 'lng': 4.492384}, 'time': {'start': '2023-08-28T09:17:16Z', 'end': '2023-08-28T09:18:16Z'}}], 'distance': 129733}, {'location': {'lat': 45.756102, 'lng': 4.498937}, 'time': {'arrival': '2023-08-28T09:23:02Z', 'departure': '2023-08-28T09:24:02Z'}, 'load': [50, 5000], 'activities': [{'jobId': 'mission_order-440', 'type': 'delivery', 'jobTag': '440', 'location': {'lat': 45.756102, 'lng': 4.498937}, 'time': {'start': '2023-08-28T09:23:02Z', 'end': '2023-08-28T09:24:02Z'}}], 'distance': 131605}, {'location': {'lat': 45.745556, 'lng': 4.487122}, 'time': {'arrival': '2023-08-28T09:33:12Z', 'departure': '2023-08-28T09:34:12Z'}, 'load': [40, 4000], 'activities': [{'jobId': 'mission_order-421', 'type': 'delivery', 'jobTag': '421', 'location': {'lat': 45.745556, 'lng': 4.487122}, 'time': {'start': '2023-08-28T09:33:12Z', 'end': '2023-08-28T09:34:12Z'}}], 'distance': 136304}, {'location': {'lat': 45.737818, 'lng': 4.546381}, 'time': {'arrival': '2023-08-28T09:55:43Z', 'departure': '2023-08-28T09:56:43Z'}, 'load': [30, 3000], 'activities': [{'jobId': 'mission_order-439', 'type': 'delivery', 'jobTag': '439', 'location': {'lat': 45.737818, 'lng': 4.546381}, 'time': {'start': '2023-08-28T09:55:43Z', 'end': '2023-08-28T09:56:43Z'}}], 'distance': 149611}, {'location': {'lat': 45.688773, 'lng': 4.802407}, 'time': {'arrival': '2023-08-28T10:51:01Z', 'departure': '2023-08-28T10:52:01Z'}, 'load': [20, 2000], 'activities': [{'jobId': 'mission_order-403', 'type': 'delivery', 'jobTag': '403', 'location': {'lat': 45.688773, 'lng': 4.802407}, 'time': {'start': '2023-08-28T10:51:01Z', 'end': '2023-08-28T10:52:01Z'}}], 'distance': 182769}, {'location': {'lat': 45.786942, 'lng': 4.83481}, 'time': {'arrival': '2023-08-28T11:18:49Z', 'departure': '2023-08-28T11:19:49Z'}, 'load': [10, 1000], 'activities': [{'jobId': 'mission_order-361', 'type': 'delivery', 'jobTag': '361', 'location': {'lat': 45.786942, 'lng': 4.83481}, 'time': {'start': '2023-08-28T11:18:49Z', 'end': '2023-08-28T11:19:49Z'}}], 'distance': 200229}, {'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'arrival': '2023-08-28T11:39:07Z', 'departure': '2023-08-28T11:42:07Z'}, 'load': [40, 4000], 'activities': [{'jobId': 'mission_order-434', 'type': 'pickup', 'jobTag': '434', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T11:39:07Z', 'end': '2023-08-28T11:40:07Z'}}, {'jobId': 'mission_order-433', 'type': 'pickup', 'jobTag': '433', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T11:40:07Z', 'end': '2023-08-28T11:41:07Z'}}, {'jobId': 'mission_order-422', 'type': 'pickup', 'jobTag': '422', 'location': {'lat': 45.760132, 'lng': 4.875581}, 'time': {'start': '2023-08-28T11:41:07Z', 'end': '2023-08-28T11:42:07Z'}}], 'distance': 205874}, {'location': {'lat': 45.812342, 'lng': 4.935005}, 'time': {'arrival': '2023-08-28T12:02:26Z', 'departure': '2023-08-28T12:03:26Z'}, 'load': [30, 3000], 'activities': [{'jobId': 'mission_order-383', 'type': 'delivery', 'jobTag': '383', 'location': {'lat': 45.812342, 'lng': 4.935005}, 'time': {'start': '2023-08-28T12:02:26Z', 'end': '2023-08-28T12:03:26Z'}}], 'distance': 217319}, {'location': {'lat': 45.835942, 'lng': 4.98561}, 'time': {'arrival': '2023-08-28T12:23:09Z', 'departure': '2023-08-28T13:24:09Z'}, 'load': [20, 2000], 'activities': [{'jobId': 'mission_order-434', 'type': 'delivery', 'jobTag': '434', 'location': {'lat': 45.835942, 'lng': 4.98561}, 'time': {'start': '2023-08-28T12:23:09Z', 'end': '2023-08-28T12:24:09Z'}}, {'jobId': 'break', 'type': 'break', 'location': {'lat': 45.835942, 'lng': 4.98561}, 'time': {'start': '2023-08-28T12:24:09Z', 'end': '2023-08-28T13:24:09Z'}}], 'distance': 233492}, {'location': {'lat': 45.77245, 'lng': 4.966339}, 'time': {'arrival': '2023-08-28T13:45:29Z', 'departure': '2023-08-28T13:46:29Z'}, 'load': [10, 1000], 'activities': [{'jobId': 'mission_order-433', 'type': 'delivery', 'jobTag': '433', 'location': {'lat': 45.77245, 'lng': 4.966339}, 'time': {'start': '2023-08-28T13:45:29Z', 'end': '2023-08-28T13:46:29Z'}}], 'distance': 250464}, {'location': {'lat': 45.694678, 'lng': 4.960346}, 'time': {'arrival': '2023-08-28T14:00:45Z', 'departure': '2023-08-28T14:01:45Z'}, 'load': [0, 0], 'activities': [{'jobId': 'mission_order-422', 'type': 'delivery', 'jobTag': '422', 'location': {'lat': 45.694678, 'lng': 4.960346}, 'time': {'start': '2023-08-28T14:00:45Z', 'end': '2023-08-28T14:01:45Z'}}], 'distance': 262153}, {'location': {'lat': 45.66291, 'lng': 4.95721}, 'time': {'arrival': '2023-08-28T14:14:08Z', 'departure': '2023-08-28T14:14:08Z'}, 'load': [0, 0], 'activities': [{'jobId': 'arrival', 'type': 'arrival', 'location': {'lat': 45.66291, 'lng': 4.95721}, 'time': {'start': '2023-08-28T14:14:08Z', 'end': '2023-08-28T14:14:08Z'}}], 'distance': 267189}], 'statistic': {'cost': 107.50048000000001, 'distance': 267189, 'duration': 31421, 'times': {'driving': 25541, 'serving': 2280, 'waiting': 0, 'stopping': 0, 'break': 3600}}, 'shiftIndex': 0}]})
        # return
        body = {}
        token = Tutils.getHereAuthToken()
        # print(token)
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
        # print(body)
        url = "https://tourplanning.hereapi.com/v3/problems"
        autorization = "Bearer " + token

        headers = {
            "Authorization": autorization,
            "Content-Type": "application/json"
        }

        response = post(url, json=body, headers=headers)
        if response.status_code == 200:
            print(response.json()) 
            self.generate_tours(response.json())
            self._calc_tour_route()
      
        

        