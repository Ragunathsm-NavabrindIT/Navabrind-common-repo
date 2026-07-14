from odoo import models, fields


class SmartSearchAttribute(models.Model):

    _name = "smart.search.attribute"
    _description = "Smart Search Attribute"

    name = fields.Char()

    value = fields.Text()

    result_id = fields.Many2one(
        "smart.search.result",
        string="Search Result",
        ondelete="cascade"
    )