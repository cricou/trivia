# -*- coding: utf-8 -*-

{
    'name' : 'Trivia TMS',
    'author': "RICOU Cyril",
    'version': '0.1',
    # 'category': '',
    'depends' : ['mail','fleet'],
    'description': """Trivia Transports Management System""",
    'data': [
        'security/ir.model.access.csv',
        'data/mission_order_data.xml',
        'data/tour_data.xml',
        'views/res_config_settings_view.xml',
        'views/menu.xml',
        'views/tour_plan_fleet_shift_view.xml',
        'views/tour_plan_fleet_view.xml',
        'views/tour_plan_view.xml',
        'views/tour_view.xml',
        'views/poi_view.xml',
        'views/mission_order_view.xml',
        'views/semi_trailer_view.xml',
        'views/fleet_vehicle_view.xml',
        'views/tour_step_view.xml',
        'views/tour_skill_view.xml',
        'views/tour_profile_view.xml',
        'views/tour_vehicle_type_view.xml'
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    # 'license': 'LGPL-3',
}
