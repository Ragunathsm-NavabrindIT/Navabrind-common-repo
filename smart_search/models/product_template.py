from odoo import models, fields
from odoo.exceptions import UserError

from ..services.ezbase_service import EZBaseService

import logging
import requests
import base64

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):

    _inherit = "product.template"

    smart_search_result_id = fields.Many2one(
        "smart.search.result",
        string="Smart Search Result"
    )

    # =====================================================
    # FETCH PRODUCT DETAILS
    # =====================================================

    def action_fetch_product_details(self):

        self.ensure_one()

        search_value = (
            self.barcode
            or self.default_code
            or self.name
        )

        _logger.info(
            "SEARCH VALUE: %s",
            search_value
        )

        if not search_value:
            raise UserError(
                "No Barcode / Internal Reference found."
            )

        # =================================================
        # CONFIG
        # =================================================

        config = self.env[
            "smart.search.config"
        ].search([], limit=1)

        if not config:
            raise UserError(
                "Smart Search Config not found. Please create a configuration."
            )

        _logger.info(
            "USING SMART SEARCH CONFIG: %s",
            config.name
        )

        # =================================================
        # SERVICE
        # =================================================

        try:
            service = EZBaseService(
                config.ez_category1_id,
                config.ez_category2_id,
                config.ez_username,
                config.ez_password
            )
        except ValueError as e:
            raise UserError(str(e))

        parsed_data = service.search_product(
            search_value
        )

        if not parsed_data:
            raise UserError(
                "Product not found on EZ Base"
            )

        # =================================================
        # DELETE OLD RESULT
        # =================================================

        if self.smart_search_result_id:
            self.smart_search_result_id.unlink()

        # =================================================
        # CREATE RESULT
        # =================================================

        result = self.env[
            "smart.search.result"
        ].create({
            "name": parsed_data.get(
                "product_name"
            ),
            "product_name": parsed_data.get(
                "product_name"
            ),
            "searched_value": search_value,
            "product_url": parsed_data.get(
                "product_url"
            ),
            "source_website": "EZ Base",
            "image_count": len(
                parsed_data.get("images", [])
            ),
            "product_id": self.id,
        })

        # =================================================
        # SAVE IMAGES
        # =================================================

        primary_image = False

        for image in parsed_data.get(
            "images",
            []
        ):

            try:

                image_content = requests.get(
                    image["url"],
                    timeout=60
                ).content

                image_base64 = base64.b64encode(
                    image_content
                ).decode("utf-8")

                if not primary_image:
                    primary_image = image_base64

                self.env["smart.search.image"].create({
                    "result_id": result.id,
                    "name": image.get("name"),
                    "image_url": image.get("url"),
                    "image": image_base64,
                })

            except Exception as image_error:

                _logger.exception(
                    "IMAGE DOWNLOAD ERROR: %s",
                    str(image_error)
                )

        if primary_image:
            self.image_1920 = primary_image

        # =================================================
        # SAVE ATTRIBUTES
        # =================================================

        for attribute in parsed_data.get(
            "attributes",
            []
        ):

            self.env["smart.search.attribute"].create({
                "result_id": result.id,
                "name": attribute.get("name"),
                "value": attribute.get("value"),
            })

        # =================================================
        # LINK RESULT
        # =================================================

        self.smart_search_result_id = result.id

        # =================================================
        # OPEN RESULT
        # =================================================

        return {
            "type": "ir.actions.act_window",
            "name": "Smart Search Result",
            "res_model": "smart.search.result",
            "view_mode": "form",
            "res_id": result.id,
            "target": "current",
        }
