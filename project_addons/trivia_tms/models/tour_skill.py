from odoo import api, fields, models, _

class TriviaTourSkills(models.Model):
    _name = 'trivia.tour.skill'
    _description = 'TRIVIA Tour Skill'

    name = fields.Char(sting="Name")
