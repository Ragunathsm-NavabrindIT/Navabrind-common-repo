import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
import json
_logger = logging.getLogger(__name__)

# --- CONFIGURATION ... ---
TRIGGER_API_KEY = 'tr_prod_7ePqzXb9sWosq2amdx4D'  
TASK_IDENTIFIER = "product-enrichment"          
TRIGGER_API_URL = f"https://api.trigger.dev/api/v1/tasks/{TASK_IDENTIFIER}/trigger"


class AIEnrichmentWizard(models.TransientModel):
    _name = 'ai.enrichment.wizard'
    _description = 'AI Enrichment Wizard'

    provider = fields.Selection(
        selection=lambda self: self._get_providers(),
        string="AI Provider",
        required=True
    )

    config_id = fields.Many2one(
        'ai.enrichment.config',
        string="AI Model",
        required=True,
        domain="[('provider', '=', provider)]" 
    )

    update_field = fields.Selection(
        [('description', 'Description')], 
        string="Field to Update", 
        required=True, 
        default='description'
    )

    product_ids = fields.Many2many('product.product', string="Products")
    product_count = fields.Integer(string="Product Count", compute="_compute_product_count")
    
    prompt_type_config = fields.Many2one('ai.prompt.type', string="Prompt Type")


    @api.model
    def _get_providers(self):
        """Return only providers configured in ai.enrichment.config"""
        providers = self.env['ai.enrichment.config'].search([]).mapped('provider')
        return [(p, dict(self.env['ai.enrichment.config'].fields_get(allfields=['provider'])['provider']['selection'])[p]) for p in set(providers)]
    
    @api.model
    def _get_prompt_types(self):
        """Return only prompt types that have been created as records"""
        records = self.env['ai.prompt.type'].search([]).mapped('name')
        # return [(p, dict(self.env['ai.prompt.type'].fields_get(allfields=['name'])['name']['selection'])[p]) for p in set(records)]

    @api.onchange('provider')
    def _onchange_provider(self):
        self.config_id = False

    @api.depends('product_ids')
    def _compute_product_count(self):
        for rec in self:
            rec.product_count = len(rec.product_ids)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids')
        latest_prompt_type = self.env['ai.prompt.type'].search([], order='create_date desc', limit=1)
        if latest_prompt_type:
            res['prompt_type_config'] = latest_prompt_type.id
        if active_ids:
            if active_model == 'product.product':
                valid_product_ids = [pid for pid in active_ids if self.env['product.product'].browse(pid).exists()]
                res['product_ids'] = [(6, 0, valid_product_ids)]
            elif active_model == 'product.template':
                templates = self.env['product.template'].browse(active_ids).exists()
                if templates:
                    products = templates.product_variant_ids
                    res['product_ids'] = [(6, 0, products.ids)]
        return res

    # --- THIS METHOD IS NOW CORRECTLY INDENTED ---
    def action_enrich(self):
        if not self.product_ids:
            raise UserError(_("No products selected for enrichment."))
        products_payload = []
        for product in self.product_ids:
            products_payload.append({
                "id": product.id, "name": product.name, "sku": product.default_code,
                "list_price": product.list_price, "standard_price": product.standard_price,
                "hsn_code": getattr(product, "l10n_in_hsn_code", False),
                "tracking": getattr(product.product_tmpl_id, "tracking", "none"),
                "supplier_taxes": [tax.name for tax in product.supplier_taxes_id],
                "sales_taxes": [tax.name for tax in product.taxes_id],
                "sale_ok": product.sale_ok, "purchase_ok": product.purchase_ok,
            })
        
        event_payload = {
            "name": "product.enrich", "payload": {"products": products_payload},
            "context": {"source": "odoo","odoo_url": "https://demo.odoopim.com" , "odoo_db": self.env.cr.dbname, "odoo_username": "admin", "    ": "V1a^R@ZracQYpaRu"},
            "ai": { "provider": self.config_id.provider, "model": self.config_id.code, "token": self.config_id.api_token,
                    "url": self.config_id.api_url, "key": self.config_id.api_key, },
            "prompt_type": {
                "type": self.prompt_type_config.name if self.prompt_type_config else ''},
            "count": {"product": str(len(products_payload))},
            "update_attribute": {"fields": self.update_field}
        }

        run_id = None
        try:
            # self.write({'loading': True})
            # self.env.cr.commit()

            _logger.info("Sending data to Trigger.dev task: %s", TASK_IDENTIFIER)
            _logger.info("Trigger Payload: %s", json.dumps({"payload": event_payload}, indent=2))
            
            response = requests.post(
                TRIGGER_API_URL,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {TRIGGER_API_KEY}"},
                json={"payload": event_payload},
                timeout=15
            )
            response.raise_for_status()
            
            response_json = response.json()
            run_id = response_json.get('id')
            _logger.info("Trigger.dev task started successfully. Run ID: %s", run_id)
            
            if run_id:
                self.env['ai.enrichment.queue.log'].create({
                    'name': run_id,
                    'config_id': self.config_id.id,
                    'product_ids': [(6, 0, self.product_ids.ids)],
                    'prompt_type': self.prompt_type_config.name,
                    'update_field': self.update_field,
                    'state': 'queued',
                })

        except requests.exceptions.RequestException as e:
            # self.write({'loading': False})
            _logger.error("Failed to trigger task: %s", e)
            if e.response is not None:
                raise UserError(_("Failed to send data to enrichment service. Server responded with: %s") % e.response.text)
            else:
                raise UserError(_("Failed to send data to enrichment service. Error: %s") % e)        

    # Optionally, you can return a notification to the user
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Enrichment process started successfully.'),
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window_close'
                }
            }
        }


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_push_to_channel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('AI Enrichment'),
            'res_model': 'ai.enrichment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_ids': self.env.context.get('active_ids', self.ids),
                'active_model': self.env.context.get('active_model', self._name),
            }
        }