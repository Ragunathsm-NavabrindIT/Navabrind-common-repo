import logging
import requests
import base64

from .parser import EZBaseParser

_logger = logging.getLogger(__name__)

# Try to import Selenium for JavaScript rendering
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    _logger.warning("Selenium not available - will use fallback methods")


class EZBaseService:

    BASE_URL = "https://www.ez-catalog.nl"
    LOGIN_URL = "https://www.ez-catalog.nl/Account/LogOn"

    def __init__(self, category1_id=None, category2_id=None, username="", password=""):
        """Initialize EZBaseService for product search.
        
        Note: Category IDs are kept for backward compatibility but are not used
        for actual searches. EZBase search finds products in any category.
        
        Args:
            category1_id: Deprecated - not used for search
            category2_id: Deprecated - not used for search
            username: Optional username for authentication
            password: Optional password for authentication
        """

        self.category1_id = category1_id
        self.category2_id = category2_id
        self.username = username
        self.password = password

        _logger.info(
            "EZBaseService initialized - using EZBase search (categories not used)"
        )

        self.session = requests.Session()
        # Set a user agent to appear as a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    # =====================================================
    # LOGIN
    # =====================================================

    def login(self):

        if not self.username or not self.password:
            _logger.info("No credentials provided, attempting without login")
            return True

        try:

            # First, get the login page to extract any CSRF tokens
            response = self.session.get(
                self.LOGIN_URL,
                timeout=60
            )

            payload = {
                "UserName": self.username,
                "Password": self.password,
            }

            response = self.session.post(
                self.LOGIN_URL,
                data=payload,
                timeout=60,
                allow_redirects=True
            )

            _logger.info(
                "LOGIN STATUS: %s",
                response.status_code
            )

            _logger.info(
                "LOGIN FINAL URL: %s",
                response.url
            )

            # Check if login was successful by looking for the login form in response
            if "LogOn" in response.url or "Account" in response.url:
                _logger.warning("Login may have failed, redirected to login page")
                return False

            return response.status_code == 200

        except Exception as e:

            _logger.exception(
                "LOGIN ERROR: %s",
                str(e)
            )

            return False

    # =====================================================
    # SEARCH PRODUCT WITH JAVASCRIPT (Selenium)
    # =====================================================

    def search_product_with_selenium(self, search_term):
        """Search for a product using Selenium to render JavaScript.
        
        This method actually clicks the 'Zoeken' button and waits for results.
        
        Args:
            search_term: Product code to search for
            
        Returns:
            str: URL of the first product found, or None
        """
        
        if not SELENIUM_AVAILABLE:
            _logger.warning("Selenium not available for JavaScript search")
            return None
        
        driver = None
        
        try:
            _logger.info("Starting Selenium search for: %s", search_term)
            
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in background
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Create driver
            driver = webdriver.Chrome(options=chrome_options)
            
            # Load search page
            search_url = f"{self.BASE_URL}/Search"
            _logger.info("Loading search page: %s", search_url)
            
            driver.get(search_url)
            
            # Find and fill the search input
            _logger.info("Looking for search input field")
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='q']"))
            )
            
            _logger.info("Found search input, entering search term: %s", search_term)
            search_input.clear()
            search_input.send_keys(search_term)
            
            # Find and click the Zoeken button
            _logger.info("Looking for Zoeken button")
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Zoeken')]"))
            )
            
            _logger.info("Found Zoeken button, clicking it")
            search_button.click()
            
            # Wait for product results to load
            _logger.info("Waiting for search results to load")
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[onclick*='/Article/']"))
            )
            
            # Get the page HTML
            page_source = driver.page_source
            
            _logger.info("Search results loaded, parsing HTML")
            
            # Parse the results
            parser = EZBaseParser(page_source)
            search_result = parser.parse_search_results()
            
            if search_result:
                product_url = search_result.get("first_product_url")
                _logger.info("SELENIUM SEARCH FOUND: %s", product_url)
                return product_url
            
            _logger.warning("SELENIUM SEARCH: No product found in results")
            return None
            
        except Exception as e:
            _logger.exception(
                "SELENIUM SEARCH ERROR: %s",
                str(e)
            )
            return None
            
        finally:
            if driver:
                try:
                    driver.quit()
                    _logger.info("Selenium driver closed")
                except Exception as e:
                    _logger.warning("Error closing Selenium driver: %s", str(e))

    # =====================================================
    # SEARCH PRODUCT
    # =====================================================

    def search_product(self, search_term):
        """Search for a product by EAN or product code.
        
        First tries JavaScript-based search with Selenium (clicks Zoeken button).
        Falls back to direct URL methods if Selenium is unavailable or fails.
        
        Args:
            search_term: EAN code or product code to search for
            
        Returns:
            dict: Parsed product data including images and attributes
        """

        try:

            _logger.info(
                "SEARCHING FOR PRODUCT: %s",
                search_term
            )
            
            # Strategy 1: Try Selenium-based search with JavaScript rendering
            if SELENIUM_AVAILABLE:
                _logger.info("STRATEGY 1: Trying Selenium-based search")
                
                product_link = self.search_product_with_selenium(search_term)
                
                if product_link:
                    _logger.info(
                        "SELENIUM SEARCH SUCCESSFUL: %s",
                        product_link
                    )
                    
                    # Fetch the product page
                    response = self.session.get(
                        product_link,
                        timeout=60
                    )
                    
                    _logger.info(
                        "FETCHED PRODUCT PAGE: %s",
                        response.url
                    )
                    
                    parser = EZBaseParser(response.text)
                    parsed_data = parser.parse()
                    parsed_data["product_url"] = response.url
                    
                    return parsed_data
                
                _logger.warning("SELENIUM SEARCH FAILED, trying fallback methods")
            else:
                _logger.warning("SELENIUM NOT AVAILABLE, using fallback methods")

            # Attempt login first (for fallback methods)
            login_success = self.login()

            _logger.info(
                "LOGIN SUCCESS: %s",
                login_success
            )

            # Strategy 2: Try regular search with direct URLs
            search_url = f"{self.BASE_URL}/Search"
            
            search_params = {
                "q": search_term
            }

            _logger.info(
                "STRATEGY 2: Trying regular search URL"
            )

            response = self.session.get(
                search_url,
                params=search_params,
                timeout=60
            )

            _logger.info(
                "SEARCH RESPONSE URL: %s",
                response.url
            )

            # Check if search redirected directly to product
            if "/Article/" in response.url:
                _logger.info(
                    "SEARCH REDIRECTED TO PRODUCT PAGE: %s",
                    response.url
                )
                parser = EZBaseParser(response.text)
                parsed_data = parser.parse()
                parsed_data["product_url"] = response.url
                return parsed_data

            # Try to parse search results
            parser = EZBaseParser(response.text)
            search_result = parser.parse_search_results()

            if search_result:
                product_link = search_result.get("first_product_url")
                
                if product_link:
                    _logger.info(
                        "FOUND PRODUCT LINK IN SEARCH: %s",
                        product_link
                    )

                    response = self.session.get(
                        product_link,
                        timeout=60
                    )

                    _logger.info(
                        "FETCHED PRODUCT PAGE: %s",
                        response.url
                    )

                    parser = EZBaseParser(response.text)
                    parsed_data = parser.parse()
                    parsed_data["product_url"] = response.url

                    return parsed_data

            _logger.warning(
                "SEARCH: No product links found in search results"
            )
            
            # Strategy 3: Try direct URL as last resort
            _logger.info(
                "STRATEGY 3: Trying direct product URL"
            )
            
            direct_url = f"{self.BASE_URL}/Article/0/0/{search_term}"
            
            response = self.session.get(
                direct_url,
                timeout=60
            )
            
            _logger.info(
                "DIRECT URL RESPONSE: %s",
                response.url
            )
            
            if response.status_code == 200 and "/Article/" in response.url:
                parser = EZBaseParser(response.text)
                parsed_data = parser.parse()
                parsed_data["product_url"] = response.url
                
                _logger.info(
                    "DIRECT URL SUCCEEDED: %s",
                    response.url
                )
                
                return parsed_data

            return None

        except Exception as e:

            _logger.exception(
                "EZBASE SEARCH ERROR: %s",
                str(e)
            )

            return None