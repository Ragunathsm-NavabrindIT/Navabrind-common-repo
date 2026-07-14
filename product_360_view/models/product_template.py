from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_360_image_ids = fields.One2many(
        'product.image.360', 'product_tmpl_id', string="360 Images"
    )
    
    product_360_ids_json = fields.Json(compute='_compute_360_json')

    @api.depends('product_360_image_ids', 'product_360_image_ids.sequence', 'product_360_image_ids.name')
    def _compute_360_json(self):
        for record in self:
            valid_ids = []
            # Sort by Sequence first, then by Name (Filename)
            images = record.product_360_image_ids.sorted(key=lambda r: (r.sequence, r.name))
            
            for img in images:
                if isinstance(img.id, int):
                    valid_ids.append(img.id)
            
            record.product_360_ids_json = valid_ids