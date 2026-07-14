from odoo import models, fields


class SmartSearchResult(models.Model):

    _name = "smart.search.result"
    _description = "Smart Search Result"

    name = fields.Char()

    product_name = fields.Char()

    searched_value = fields.Char()

    product_url = fields.Char()

    source_website = fields.Char()

    image_count = fields.Integer()

    product_id = fields.Many2one(
        "product.template",
        string="Product"
    )

    image_ids = fields.One2many(
        "smart.search.image",
        "result_id",
        string="Images"
    )

    attribute_ids = fields.One2many(
        "smart.search.attribute",
        "result_id",
        string="Attributes"
    )