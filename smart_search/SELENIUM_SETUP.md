# Selenium Setup for EZBase Search

The Smart Search module can use Selenium for JavaScript-rendered search results. Selenium is **optional** but **recommended** for proper search functionality.

## Why Selenium?

EZBase search results require clicking the "Zoeken" button which triggers JavaScript. Without Selenium, the module will use fallback methods that may not work reliably.

## Installation

### 1. Install Selenium Python Package

```bash
pip install selenium
```

### 2. Install ChromeDriver

The system needs ChromeDriver to control Google Chrome/Chromium.

#### Option A: Ubuntu/Debian
```bash
sudo apt-get install chromium-chromedriver
```

#### Option B: Manual Download
1. Download from: https://chromedriver.chromium.org/
2. Extract to a location in your PATH (e.g., `/usr/local/bin/`)
3. Make executable: `chmod +x /usr/local/bin/chromedriver`

#### Option C: Docker
If running in Docker, ensure Chromium and ChromeDriver are installed in the image.

### 3. Verify Installation

```bash
which chromedriver
chromedriver --version
python -c "from selenium import webdriver; print('Selenium OK')"
```

## How It Works

1. **With Selenium**: Module loads EZBase search page, enters search term, clicks "Zoeken" button, waits for JavaScript to render results, then parses them
2. **Without Selenium**: Module uses fallback methods (direct URLs)

## Troubleshooting

### ChromeDriver not found
```
Error: 'chromedriver' executable needs to be in PATH
```
Solution: Make sure chromedriver is installed and in your PATH

### Chrome/Chromium not found
```
Error: Could not find Chrome/Chromium binary
```
Solution: Install Chrome/Chromium:
```bash
# Ubuntu/Debian
sudo apt-get install chromium-browser

# Fedora/CentOS
sudo yum install chromium
```

### Timeout waiting for elements
Check your EZBase account has valid credentials configured in Smart Search Config.

## Performance Notes

- Selenium search takes 15-20 seconds per search (includes browser startup)
- Direct URL fallback is instant but may fail for some products
- Results are cached in `smart.search.result` model
