from odoo import models, fields


class SmartSearchImage(models.Model):

    _name = "smart.search.image"
    _description = "Smart Search Image"

    name = fields.Char()

    image = fields.Image()

    image_url = fields.Char()

    result_id = fields.Many2one(
        "smart.search.result",
        string="Search Result",
        ondelete="cascade"
    )