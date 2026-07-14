from odoo import models, fields


class SmartSearchConfig(models.Model):
    _name = "smart.search.config"
    _description = "Smart Search Configuration"

    name = fields.Char(
        required=True,
        default="EZ Base Configuration"
    )

    active = fields.Boolean(
        default=True
    )

    # ==========================================
    # EZ BASE
    # ==========================================

    ez_base_url = fields.Char(
        string="EZ Base URL",
        default="https://ez-catalog.nl"
    )

    ez_username = fields.Char(
        string="EZ Username",
        required=True
    )

    ez_password = fields.Char(
        string="EZ Password",
        required=True
    )

    # ==========================================
    # PRODUCT FIELD
    # ==========================================

    search_field_id = fields.Many2one(
        'ir.model.fields',
        string="Product Search Field",
        domain=[
            ('model', '=', 'product.template')
        ],
        required=True,
        ondelete='cascade',
    )