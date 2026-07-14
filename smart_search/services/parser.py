from bs4 import BeautifulSoup
import logging

_logger = logging.getLogger(__name__)


class EZBaseParser:

    def __init__(self, html):

        self.html = html
        self.soup = BeautifulSoup(
            html,
            "html.parser"
        )

    # =====================================================
    # MAIN PARSE
    # =====================================================

    def parse(self):

        return {
            "product_name": self.get_product_name(),
            "images": self.get_images(),
            "attributes": self.get_attributes(),
        }

    # =====================================================
    # PARSE SEARCH RESULTS
    # =====================================================

    def parse_search_results(self):
        """Parse search results page to find the first product link.
        
        EZBase search results are rendered with JavaScript, so links may be in:
        - onclick handlers
        - data attributes
        - JavaScript function calls
        - Hidden form inputs
        
        Returns:
            dict: Dictionary with 'first_product_url' key pointing to the product
        """
        
        try:
            _logger.info("Starting to parse search results HTML")
            
            # Strategy 1: Look for divs with onclick handlers that contain /Article/
            all_divs = self.soup.find_all("div")
            onclick_links = []
            
            for div in all_divs:
                onclick = div.get("onclick", "")
                if onclick and "/Article/" in onclick:
                    onclick_links.append(div)
                    _logger.debug("Found div with /Article/ in onclick: %s", onclick[:100])
            
            if onclick_links:
                _logger.info("FOUND %s DIVS WITH /Article/ IN ONCLICK", len(onclick_links))
                
                first_onclick = onclick_links[0].get("onclick", "")
                # Extract URL from onclick - usually looks like: window.location='/Article/...'
                import re
                match = re.search(r"['\"](/Article/[^'\"]+)['\"]", first_onclick)
                
                if match:
                    product_url = match.group(1)
                    if not product_url.startswith("http"):
                        product_url = "https://www.ez-catalog.nl" + product_url
                    
                    _logger.info(
                        "FOUND PRODUCT URL FROM ONCLICK: %s",
                        product_url
                    )
                    
                    return {
                        "first_product_url": product_url
                    }
            
            # Strategy 2: Look for <a> tags with /ArtLink onclick (common pattern)
            artlink_elements = [
                elem for elem in all_divs 
                if elem.get("onclick", "").startswith("/ArtLink")
            ]
            
            if artlink_elements:
                _logger.info("FOUND %s ELEMENTS WITH /ArtLink ONCLICK", len(artlink_elements))
                
                onclick = artlink_elements[0].get("onclick", "")
                _logger.debug("ArtLink onclick: %s", onclick[:100])
                
                # Parse /ArtLink parameters
                import re
                match = re.search(r"/ArtLink[^']*['\"]?([^'\"]*)['\"]?", onclick)
                if match:
                    product_code = match.group(1)
                    _logger.info("EXTRACTED PRODUCT CODE FROM ARTLINK: %s", product_code)
            
            # Strategy 3: Look for clickable elements with data attributes
            clickable = self.soup.find_all(
                ["div", "a", "span"], 
                attrs={"data-article-id": True}
            )
            
            if clickable:
                _logger.info("FOUND %s ELEMENTS WITH data-article-id", len(clickable))
                
                for elem in clickable[:3]:
                    article_id = elem.get("data-article-id", "")
                    _logger.debug("Article ID: %s", article_id)
                    
                    if article_id:
                        # Try to construct product URL
                        product_url = f"https://www.ez-catalog.nl/Article/0/0/{article_id}"
                        _logger.info(
                            "CONSTRUCTED PRODUCT URL FROM data-article-id: %s",
                            product_url
                        )
                        
                        return {
                            "first_product_url": product_url
                        }
            
            # Strategy 5: Look for product data in script tags (JSON)
            scripts = self.soup.find_all("script")
            
            for script in scripts:
                script_content = script.string
                if not script_content:
                    continue
                
                # Look for article IDs in JSON or JavaScript object notation
                import re
                
                # Try to find patterns like "articleId":"1234567"
                article_match = re.search(r'["\']?articleId["\']?\s*[:=]\s*["\']?(\d+)["\']?', script_content)
                if article_match:
                    article_id = article_match.group(1)
                    _logger.info("FOUND ARTICLE ID IN SCRIPT: %s", article_id)
                    
                    # Try different URL patterns
                    possible_urls = [
                        f"https://www.ez-catalog.nl/Article/0/0/{article_id}",
                        f"https://www.ez-catalog.nl/Article/{article_id}",
                    ]
                    
                    _logger.info(
                        "CONSTRUCTED PRODUCT URL FROM SCRIPT DATA: %s",
                        possible_urls[0]
                    )
                    
                    return {
                        "first_product_url": possible_urls[0]
                    }
                
                # Try to find /Article/ URLs in JavaScript strings
                article_url_match = re.search(r'/Article/\d+/\d+/[^\s"\')<>]+', script_content)
                if article_url_match:
                    product_path = article_url_match.group(0)
                    product_url = "https://www.ez-catalog.nl" + product_path
                    
                    _logger.info(
                        "FOUND PRODUCT URL IN SCRIPT: %s",
                        product_url
                    )
                    
                    return {
                        "first_product_url": product_url
                    }
            
            # Strategy 6: Look for hidden inputs or data attributes with product IDs
            hidden_inputs = self.soup.find_all("input", type="hidden")
            
            for inp in hidden_inputs:
                name = inp.get("name", "").lower()
                value = inp.get("value", "")
                
                if ("article" in name or "product" in name) and value:
                    _logger.debug("Found hidden input: %s=%s", name, value)
                    
                    if "/" in value and len(value) > 5:
                        # Might be an article ID or path
                        if not value.startswith("http"):
                            if "/" in value:
                                product_url = "https://www.ez-catalog.nl" + value
                            else:
                                product_url = f"https://www.ez-catalog.nl/Article/0/0/{value}"
                        else:
                            product_url = value
                        
                        _logger.info(
                            "FOUND PRODUCT URL FROM HIDDEN INPUT: %s",
                            product_url
                        )
                        
                        return {
                            "first_product_url": product_url
                        }
            
            _logger.warning(
                "NO PRODUCT LINKS FOUND IN SEARCH RESULTS - "
                "Tried onclick handlers, data attributes, and clickable elements. "
                "Total divs: %s",
                len(all_divs)
            )
            
            # Log samples for debugging
            if all_divs:
                _logger.info(
                    "Sample div onclicks (first 5): %s",
                    [d.get("onclick", "")[:80] for d in all_divs[:5] if d.get("onclick")]
                )
            
            return None
            
        except Exception as e:
            _logger.exception(
                "ERROR PARSING SEARCH RESULTS: %s",
                str(e)
            )
            return None

    # =====================================================
    # PRODUCT NAME
    # =====================================================

    def get_product_name(self):

        title = self.soup.find("title")

        if title:
            return title.get_text(strip=True)

        return "Unknown Product"

    # =====================================================
    # IMAGES
    # =====================================================

    def get_images(self):

        images = []

        gallery = self.soup.find(
            "div",
            id="imagePreviewGallery"
        )

        if not gallery:
            _logger.warning(
                "IMAGE GALLERY NOT FOUND"
            )
            return images

        image_links = gallery.find_all(
            "a",
            class_="asset"
        )

        _logger.info(
            "FOUND IMAGE LINKS: %s",
            len(image_links)
        )

        added_urls = set()

        for link in image_links:

            image_url = link.get("href")

            if not image_url:
                continue

            if image_url in added_urls:
                continue

            added_urls.add(image_url)

            filename = image_url.split("/")[-1]

            images.append({
                "name": filename,
                "url": image_url,
            })

        _logger.info(
            "FINAL IMAGE COUNT: %s",
            len(images)
        )

        return images

    # =====================================================
    # ATTRIBUTES
    # =====================================================

    def get_attributes(self):

        attributes = []

        table = self.soup.find(
            "table",
            class_="table"
        )

        if not table:
            _logger.warning(
                "ATTRIBUTE TABLE NOT FOUND"
            )
            return attributes

        rows = table.find_all("tr")

        _logger.info(
            "FOUND ATTRIBUTE ROWS: %s",
            len(rows)
        )

        for row in rows:

            cols = row.find_all("td")

            if len(cols) < 3:
                continue

            name = cols[1].get_text(strip=True)
            value = cols[2].get_text(strip=True)

            if not name:
                continue

            if not value:
                continue

            attributes.append({
                "name": name,
                "value": value,
            })

        _logger.info(
            "FINAL ATTRIBUTE COUNT: %s",
            len(attributes)
        )

        return attributes