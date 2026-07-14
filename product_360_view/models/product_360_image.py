from odoo import models, fields

class Product360Image(models.Model):
    _name = 'product.image.360'
    _description = 'Product 360 Images'
    # Sort by Name (Filename) automatically
    _order = 'name, sequence, id' 

    name = fields.Char(string="Name")
    image = fields.Image(string="Image", max_width=1920, max_height=1920, required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    product_tmpl_id = fields.Many2one('product.template', string="Product", ondelete='cascade')