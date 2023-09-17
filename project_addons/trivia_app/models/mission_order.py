from odoo import models, fields, api
import os
import requests

class MissionOrderInherited(models.Model):
    _inherit = 'mission.order'
    _name = _inherit

    @api.onchange('state')
    def onchange_state(self):
        self.ensure_one()
        if self.state == 'in_progress' and self.driver_id:
            subscriptions = []
            user_id = self.env['res.users'].search([('partner_id', '=', self.driver_id.id)])
            for subscription in user_id.one_signal_subscription_ids:
                subscriptions.append(subscription.subscription_ref)
            
            if subscriptions:
                print(subscriptions)
                app_id = os.environ['ONE_SIGNAL_APP_ID']
                rest_api_key = os.environ['ONE_SIGNAL_API_KEY']

                url = "https://onesignal.com/api/v1/notifications"
                loading = self.loading.full_address
                delivery = self.delivery.full_address
                contents = f"""Loading: {loading}\nDelivery: {delivery}"""
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'Basic ' + rest_api_key,
                }

                payload = {
                    'app_id': app_id,
                    'include_player_ids': subscriptions,
                    'contents': {'en': contents},
                    'headings': {'en': 'Ordre de mission'},
                }

                response = requests.post(url, headers=headers, json=payload)
                print("ezeze")
                print(response)
                print(response.text)