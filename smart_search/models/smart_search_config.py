from odoo import models, fields

import logging

_logger = logging.getLogger(__name__)


class SmartSearchConfig(models.Model):
    _name = "smart.search.config"
    _description = "Smart Search Config"

    name = fields.Char(
        default="Default"
    )

    active = fields.Boolean(
        default=True
    )

    ez_base_url = fields.Char(
        string="EZ Base URL",
        default="https://www.ez-catalog.nl",
    )

    ez_username = fields.Char(
        string="Username",
    )

    ez_password = fields.Char(
        string="Password",
    )

    search_field_id = fields.Many2one(
        "ir.model.fields",
        string="Search Field",
        domain=[
            ("model", "=", "product.template")
        ],
        ondelete="set null",
    )

    ez_category1_id = fields.Char(
        string="EZ Category 1 ID",
        required=False,
        help="(Deprecated) Not used for search. EZBase search finds products in any category automatically."
    )

    ez_category2_id = fields.Char(
        string="EZ Category 2 ID",
        required=False,
        help="(Deprecated) Not used for search. EZBase search finds products in any category automatically."
    )

    def write(self, values):
        """Log when configuration is updated"""
        result = super().write(values)
        
        for config in self:
            _logger.info(
                "SmartSearchConfig updated: %s",
                config.name
            )
        
        return result