import requests
import json
import logging
from odoo import api, fields, models, _
import pytz 

_logger = logging.getLogger(__name__)

# --- CHANGE: Hardcoded API Key ---
# Note: Storing keys in code is not recommended for production environments.
# Consider using Odoo's System Parameters for better security and flexibility.
TRIGGER_API_KEY = 'tr_prod_7ePqzXb9sWosq2amdx4D'

class AIEnrichmentQueueLog(models.Model):
    _name = 'ai.enrichment.queue.log'
    _description = 'AI Enrichment Queue Log'
    _order = 'create_date desc'

    name = fields.Char(string="Run ID", required=True, readonly=True, index=True)
    reference = fields.Char(string="Reference", readonly=True)
    
    state = fields.Selection([
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ], string="Sync Status", default='queued', readonly=True, copy=False)

    config_id = fields.Many2one('ai.enrichment.config', string="AI Configuration", readonly=True)
    product_ids = fields.Many2many('product.product', string="Products", readonly=True)
    product_count = fields.Integer(string="Total Products", compute="_compute_product_count", store=True)
    
    type = fields.Char(string="Type", default="Product Ai Enrichment", readonly=True)

    prompt_type = fields.Char(string="Prompt Type", readonly=True)
    update_field = fields.Char(string="Updated Field", readonly=True)

    generation_success_count = fields.Integer(string="Generation Success", readonly=True)
    generation_failed_count = fields.Integer(string="Generation Failed", readonly=True)
    update_success_count = fields.Integer(string="Odoo Update Success", readonly=True)
    update_failed_count = fields.Integer(string="Odoo Update Failed", readonly=True)
    results_json = fields.Text(string="Detailed Results (JSON)", readonly=True)
    error_message = fields.Text(string="Error Message", readonly=True)

    create_date_formatted = fields.Char(
        string="Queued", 
        compute='_compute_create_date_formatted',
        store=True # Storing is good for performance if the view will be loaded often
    )

    @api.depends('create_date')
    def _compute_create_date_formatted(self):
        for log in self:
            if log.create_date:
                user_local_time = fields.Datetime.context_timestamp(log, log.create_date)
                
                # 2. Now, format the NEW timezone-aware datetime object.
                log.create_date_formatted = "{} - {} - {} | {}".format(
                    user_local_time.strftime('%d'),
                    user_local_time.strftime('%b').upper(),
                    user_local_time.strftime('%Y'),
                    user_local_time.strftime('%I:%M %p')
                )
            else:
                log.create_date_formatted = ''

    @api.depends('product_ids')
    def _compute_product_count(self):
        for log in self:
            log.product_count = len(log.product_ids)
    
    # --- CHANGE: Removed _get_trigger_api_key method ---
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('reference'):
                vals['reference'] = self.env['ir.sequence'].next_by_code('sync.queue.code')
        return super().create(vals_list)

    def write(self, vals):
        return super().write(vals)


    def action_refresh_status(self):
        """Button action to manually refresh the status from Trigger.dev."""
        if not TRIGGER_API_KEY:
            _logger.warning("Trigger.dev API Key is not set in the model file.")
            return

        for log in self:
            if log.state not in ['queued', 'processing']:
                continue

            run_id = log.name
            url = f"https://api.trigger.dev/api/v3/runs/{run_id}"
            headers = {"Authorization": f"Bearer {TRIGGER_API_KEY}"}
            
            vals_to_write = {}
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                print("Data from trigger retrive api", data)

                trigger_status = data.get('status')
                if trigger_status in ('QUEUED', 'EXECUTING', 'PENDING'):
                    vals_to_write['state'] = 'processing'
                elif trigger_status == 'COMPLETED':
                    if data.get('isSuccess'):
                        vals_to_write['state'] = 'done'
                        output = data.get('output')
                        if output:
                            if isinstance(output, str):
                                output = json.loads(output)
                            vals_to_write.update({
                                'generation_success_count': output.get('generationSuccess', 0),
                                'generation_failed_count': output.get('generationFailed', 0),
                                'update_success_count': output.get('updateSuccess', 0),
                                'update_failed_count': output.get('updateFailedOrSkipped', 0),
                                'results_json': json.dumps(output.get('results', []), indent=2),
                            })
                    elif data.get('isFailed'):
                        vals_to_write['state'] = 'failed'
                        error = data.get('error', {})
                        vals_to_write['error_message'] = error.get('message', 'Unknown failure.')
                elif trigger_status == 'CANCELLED':
                    vals_to_write['state'] = 'failed'
                    vals_to_write['error_message'] = 'Run was cancelled.'

                # 🔥 Important: actually write changes to DB
                if vals_to_write:
                    log.write(vals_to_write)

            except requests.exceptions.RequestException as e:
                _logger.error(f"Failed to connect to Trigger.dev for run {run_id}: {e}")
            except Exception as e:
                _logger.error(f"An unexpected error occurred while processing run {run_id}: {e}")
                log.write({'state': 'failed', 'error_message': str(e)})

        """Button action to manually refresh the status from Trigger.dev."""
        # --- CHANGE: Use the static API key ---
        if not TRIGGER_API_KEY:
            _logger.warning("Trigger.dev API Key is not set in the model file.")
            return

        for log in self:
            if log.state not in ['queued', 'processing']:
                continue

            run_id = log.name
            url = f"https://api.trigger.dev/api/v3/runs/{run_id}"
            headers = {"Authorization": f"Bearer {TRIGGER_API_KEY}"}
            
            vals_to_write = {}
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                print("Data from trigger retrive api",data)

                trigger_status = data.get('status')
                if trigger_status in ('QUEUED', 'EXECUTING', 'PENDING'):
                    vals_to_write['state'] = 'processing'
                elif trigger_status == 'COMPLETED':
                    if data.get('isSuccess'):
                        vals_to_write['state'] = 'done'
                        output = data.get('output')
                        if output:
                            if isinstance(output, str):
                                output = json.loads(output)
                            vals_to_write.update({
                                'generation_success_count': output.get('generationSuccess', 0),
                                'generation_failed_count': output.get('generationFailed', 0),
                                'update_success_count': output.get('updateSuccess', 0),
                                'update_failed_count': output.get('updateFailedOrSkipped', 0),
                                'results_json': json.dumps(output.get('results', []), indent=2),
                            })
                    elif data.get('isFailed'):
                        vals_to_write['state'] = 'failed'
                        error = data.get('error', {})
                        vals_to_write['error_message'] = error.get('message', 'Unknown failure.')
                elif trigger_status == 'CANCELLED':
                    vals_to_write['state'] = 'failed'
                    vals_to_write['error_message'] = 'Run was cancelled.'


            except requests.exceptions.RequestException as e:
                _logger.error(f"Failed to connect to Trigger.dev for run {run_id}: {e}")
            except Exception as e:
                _logger.error(f"An unexpected error occurred while processing run {run_id}: {e}")
                log.write({'state': 'failed', 'error_message': str(e)})
    
    @api.model
    def _cron_check_pending_runs(self):
        """Cron job to check all queued or processing runs."""
        _logger.info("Running cron job to check pending AI enrichment runs...")
        pending_logs = self.search([('state', 'in', ['queued', 'processing'])])
        pending_logs.action_refresh_status()
        _logger.info(f"Cron job finished. Checked {len(pending_logs)} runs.")