from odoo import models, fields, api
import requests

class ResPartner(models.Model):
    _inherit = "res.partner"

    google_validated = fields.Boolean("Google Address Validated", readonly=True, copy=False)

    @api.model
    def _get_google_api_key(self):
        # Best to fetch from system parameters
        return self.env['ir.config_parameter'].sudo().get_param('google.api_key')
        # return "YOUR_GOOGLE_API_KEY"

    def action_validate_address(self):
        for partner in self:
            api_key = self._get_google_api_key()
            if not api_key:
                partner.message_post(
                    body="<b>Configuration Error:</b> Missing Google API key.",
                    subtype_xmlid="mail.mt_note"
                )
                continue

            address_parts = [
                partner.street,
                partner.street2,
                partner.city,
                partner.state_id.name,
                partner.zip,
                partner.country_id.name
            ]
            address = ", ".join(filter(None, address_parts))

            if not address.strip():
                partner.message_post(
                    body="<b>Validation Failed:</b> The address is empty.",
                    subtype_xmlid="mail.mt_note"
                )
                continue

            url = f"https://addressvalidation.googleapis.com/v1:validateAddress?key={api_key}"
            payload = {
                "address": {
                    "regionCode": partner.country_id.code if partner.country_id else "",
                    "addressLines": [partner.street or '', partner.street2 or '', f"{partner.city or ''} {partner.state_id.name or ''} {partner.zip or ''}"],
                }
            }

            try:
                response = requests.post(url, json=payload, timeout=10)
                response_data = response.json()

                if response.status_code == 200:
                    result = response_data.get("result", {})
                    verdict = result.get("verdict", {})
                    address_complete = verdict.get("addressComplete", False)

                    if address_complete:
                        partner.google_validated = True
                        partner.message_post(
                            body="<b>Google Address Validation:</b> Address was successfully validated.",
                            message_type="notification",
                            subtype_xmlid="mail.mt_note"
                        )
                    else:
                        partner.google_validated = False
                        feedback = result.get('address', {}).get('formattedAddress', 'Address appears incomplete or invalid.')
                        partner.message_post(
                            body=f"<b>Google Address Validation:</b> Validation issues found. Google suggests: <i>{feedback}</i>",
                            message_type="notification",
                            subtype_xmlid="mail.mt_note"
                        )

                else:
                    partner.google_validated = False
                    error_details = response_data.get("error", {})
                    error_message = error_details.get("message", "Unknown error.")

                    if "Unsupported region code" in error_message:
                        partner.message_post(
                            body=f"<b>Google Address Validation Error:</b> The country '{partner.country_id.name}' is not supported for validation.",
                            subtype_xmlid="mail.mt_note"

                        )
                    else:
                        partner.message_post(
                            body=f"<b>Google Address Validation Error:</b> API returned an error: {error_message}",
                            subtype_xmlid="mail.mt_note"

                        )

            except requests.exceptions.RequestException as e:
                partner.google_validated = False
                partner.message_post(
                    body=f"<b>Google Address Validation Exception:</b> Could not connect to the API. Error: {e}",
                    subtype_xmlid="mail.mt_note"
                    
                )
