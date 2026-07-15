# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    retail_price = fields.Float(
        string="Retail Price",
        compute="_compute_retail_price",
        store=False,
        help="Retail price based on the Retail Pricelist (INR)."
    )

    secondary_quantity_total = fields.Float(
        string='Total Secondary Quantity',
        compute='_compute_secondary_quantity_total',
        store=False,
        help="Shows the total secondary quantity across all internal stock locations."
    )

    @api.depends('list_price', 'categ_id')
    def _compute_retail_price(self):
        Pricelist = self.env['product.pricelist']
        retail_pricelist = Pricelist.search([('name', 'ilike', 'Retail Pricelist')], limit=1)
        for product in self:
            if not retail_pricelist:
                product.retail_price = product.list_price
                continue

            try:
                price = retail_pricelist._get_product_price(product, 1.0)
                product.retail_price = price or product.list_price
            except Exception as e:
                product.retail_price = product.list_price

    @api.depends('product_variant_ids')
    def _compute_secondary_quantity_total(self):
        for template in self:
            variants = template.product_variant_ids
            if not variants:
                template.secondary_quantity_total = 0.0
                continue

            Quant = self.env['stock.quant']
            domain = [
                ('product_id', 'in', variants.ids),
                ('location_id.usage', '=', 'internal'),
            ]

            grouped = Quant.read_group(domain, ['product_id', 'quantity', 'secondary_qty'], ['product_id'])
            template.secondary_quantity_total = sum(res.get('secondary_qty', 0.0) for res in grouped)



