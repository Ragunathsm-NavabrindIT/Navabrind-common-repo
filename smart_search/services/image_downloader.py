import base64
import logging
import requests

_logger = logging.getLogger(__name__)


def download_image(url):

    try:

        response = requests.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        return base64.b64encode(
            response.content
        )

    except Exception as e:

        _logger.exception(
            "IMAGE DOWNLOAD FAILED: %s",
            e
        )

        return False