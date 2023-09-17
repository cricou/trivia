from odoo import http
from odoo.http import request
import json
from datetime import date, datetime

class AppController(http.Controller):

    @staticmethod
    def get_mo_info(mo):
        return {
            'tz': request.env.user.tz,
            'id': mo.id,
            'name': mo.name,
            'date': mo.date.strftime('%d/%m/%Y'),
            'loading': mo.loading.full_address,
            'loading_start_date': mo.loading_start_date.strftime('%d/%m/%Y %H:%M:%S'),
            'loading_end_date': mo.loading_end_date.strftime('%d/%m/%Y %H:%M:%S'),
            'delivery': mo.delivery.full_address,
            'delivery_start_date': mo.delivery_start_date.strftime('%d/%m/%Y %H:%M:%S'),
            'delivery_end_date': mo.delivery_end_date.strftime('%d/%m/%Y %H:%M:%S'),
            'note': mo.note,
            'state': mo.state,
            'driving_time': mo.driving_time,
            'distance': round(mo.distance),
            'fuel_cost': mo.fuel_cost,
            'toll_cost': mo.toll_cost,
            'total_cost': mo.total_cost,
            'includes_ferry': mo.includes_ferry,
            'ferry_time': mo.ferry_time,
            'cargo_length': mo.cargo_length,
            'cargo_payload': mo.cargo_payload,
            }

    @http.route('/trivia_api/get_mo', type='json', auth='user', methods=['POST'])
    def get_mo(self, **kwargs):
        user = request.env.user
        mission_order_model = request.env['mission.order']
        partner_id = request.env.user.partner_id.id
        mo_list = mission_order_model.sudo().search([('state', 'in', ['in_progress','done']),('driver_id', '=', partner_id)])
        result = []
        for mo in mo_list:
            mo_info = self.get_mo_info(mo)
            result.append(mo_info)
        json_result = json.dumps(result)

        return json_result

    @http.route('/trivia_api/set_mo_done', type='json', auth='user', methods=['POST'])
    def set_mo_done(self, **kwargs):
        mission_order_model = request.env['mission.order']
        mission_order_name = kwargs['mission_order']
        print(mission_order_name)
        mission_order_id = mission_order_model.sudo().search([('name', '=', mission_order_name)])
        mission_order_id.sudo().write({
            'state': 'done'
        })
        return

    @http.route('/trivia_api/sync_attach', type='json', auth='user', methods=['POST'])
    def sync_attach(self, **kwargs):
        mission_order_model = request.env['mission.order']
        mission_order_name = kwargs['mission_order']
        print(mission_order_name)
        mission_order_id = mission_order_model.sudo().search([('name', '=', mission_order_name)])
        mission_order_id.sudo().write({
            'state': 'done'
        })
        return

    @http.route('/trivia_api/sync_attach', type='json', auth='user', methods=['POST'])
    def sync_attach(self, **kwargs):
        mission_order_name = kwargs['mission_order']
        mission_order_attachment = kwargs['attachment']
        mission_order_attachment_name = kwargs['image_name']

        # Trouver la mission order correspondante
        mission_order = request.env['mission.order'].sudo().search([('name', '=', mission_order_name)], limit=1)
        print(mission_order_name)
        if mission_order:
            # Créer une pièce jointe
            attachment = request.env['ir.attachment'].sudo().create({
                'name': mission_order_attachment_name,
                'datas': mission_order_attachment,
                'res_model': 'mission.order',
                'res_id': mission_order.id,
                'type': 'binary'
            })
            return True
        else:
            return False

    @http.route('/trivia_api/set_location', type='json', auth='user', methods=['POST'])
    def set_location(self, **kwargs):
        latitude = kwargs['latitude']
        longitude = kwargs['longitude']
        altitude = kwargs['altitude']
        accuracy = kwargs['accuracy']
        bearing = kwargs['bearing']
        speed = kwargs['speed']
        time = datetime.fromtimestamp(int(kwargs['time']) / 1000.0)

        tracking_location_model = request.env['trivia.tracking.location']
        user_id = request.env.user.id

        tracking_location_model.sudo().create({
            'user_id': user_id,
            'latitude': latitude,
            'longitude': longitude,
            'altitude': altitude,
            'accuracy': accuracy,
            'bearing': bearing,
            'speed': speed,
            'time': time,

            
        })
        return 
