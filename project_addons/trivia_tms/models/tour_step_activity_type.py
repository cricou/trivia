# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class TriviaTourStepActivityType(models.Model):
    _name = 'trivia.tour.step.activity.type'
    _description = 'TRIVIA Tour Activity Type'

    name = fields.Char()
    ref = fields.Char()
    color = fields.Char()