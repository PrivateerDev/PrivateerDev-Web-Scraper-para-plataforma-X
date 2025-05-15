import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import re

# ===== CONFIGURATION =====
PAGES = {
    "KFC México": "https://www.facebook.com/KFCMexico",
    "Little Caesars México": "https://www.facebook.com/LittleCaesarsMexico",
    "Burger King México": "https://www.facebook.com/BurgerKingMexico"
}
KEYWORDS = ['ciudad de mexico', 'cdmx', 'ciudad de méxico', 'mexico city']

# Performance settings
SCROLL_PAUSE_TIME = 10  # Seconds between scrolls (increase if getting blocked)
INITIAL_LOAD_TIME = 15  # Seconds to wait for initial page load
BETWEEN_PAGE_DELAY = 20  # Seconds between different pages
MAX_POSTS = 30  # Number of posts to collect per page
MAX_RETRIES = 3  # Retry attempts when failures occur

# Browser settings
HEADLESS_MODE = True  # Set to False to see the browser window
PROXY_SERVER = None  # Example: "http://123.456.789:8080" or None if not using proxy

# ===== MAIN CODE =====
def setup_driver():
    """Configure Chrome options and initialize WebDriver"""
    chrome_options = Options()
    
    # Basic options
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--lang=es-MX")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Stability options
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    
    # Headless mode
    if HEADLESS_MODE:
        chrome_options.add_argument("--headless=new")
    
    # Proxy configuration
    if PROXY_SERVER:
        chrome_options.add_argument(f'--proxy-server={PROXY_SERVER}')
    
    # Automatic driver management
    service = Service(ChromeDriverManager().install())
    
    return webdriver.Chrome(service=service, options=chrome_options)

def extract_engagement(text):
    """Extract numbers from engagement text"""
    if not text:
        return 0
    text = text.replace('.', '').replace(',', '')
    
    # Handle "1.2K" type values
    if 'K' in text:
        return int(float(text.replace('K', '')) * 1000
    if 'M' in text:
        return int(float(text.replace('M', '')) * 1000000
    
    numbers = re.findall(r'\d+', text)
    return int(numbers[0]) if numbers else 0

def scrape_page(driver, page_name, page_url):
    print(f"\nScraping {page_name}...")
    
    for attempt in range(MAX_RETRIES):
        try:
            driver.get(page_url)
            time.sleep(INITIAL_LOAD_TIME)
            
            # Accept cookies if popup appears (European version)
            try:
                cookie_button = driver.find_element(By.XPATH, '//div[contains(@aria-label, "Allow all cookies") or contains(text(), "Allow all cookies")]')
                cookie_button.click()
                time.sleep(3)
            except NoSuchElementException:
                pass
                
            last_height = driver.execute_script("return document.body.scrollHeight")
            posts_collected = 0
            data = []
            
            while posts_collected < MAX_POSTS:
                # Scroll down
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_PAUSE_TIME)
                
                # Check if we've reached the bottom
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("Reached end of page")
                    break
                last_height = new_height
                
                # Find all visible posts
                posts = driver.find_elements(By.XPATH, '//div[@role="article"]')
                print(f"Found {len(posts)} posts total (looking for {MAX_POSTS - posts_collected} more)")
                
                for post in posts[-10:]:  # Only check newest posts to avoid duplicates
                    try:
                        # Get post text (if available)
                        try:
                            post_text = post.find_element(
                                By.XPATH, './/div[contains(@data-ad-preview, "message") or contains(@class, "userContent")]'
                            ).text.lower()
                        except NoSuchElementException:
                            continue
                            
                        # Check if post contains our keywords
                        if not any(keyword in post_text for keyword in KEYWORDS):
                            continue
                            
                        # Get engagement metrics
                        try:
                            reactions = post.find_element(
                                By.XPATH, './/span[contains(@aria-label, "reaction") or contains(@aria-label, "Reacciones")]'
                            ).get_attribute("aria-label")
                            reactions_count = extract_engagement(reactions)
                        except NoSuchElementException:
                            reactions_count = 0
                            
                        try:
                            comments = post.find_element(
                                By.XPATH, './/span[contains(@aria-label, "comment") or contains(@aria-label, "Comentarios")]'
                            ).get_attribute("aria-label")
                            comments_count = extract_engagement(comments)
                        except NoSuchElementException:
                            comments_count = 0
                            
                        try:
                            shares = post.find_element(
                                By.XPATH, './/span[contains(text(), "compart") or contains(text(), "share")]'
                            ).text
                            shares_count = extract_engagement(shares)
                        except NoSuchElementException:
                            shares_count = 0
                            
                        # Get post date
                        try:
                            post_date = post.find_element(
                                By.XPATH, './/a[contains(@href, "/posts/")]//span//span'
                            ).text
                        except NoSuchElementException:
                            post_date = "Unknown"
                        
                        # Add to results
                        data.append({
                            "page": page_name,
                            "date": post_date,
                            "text": post_text[:200],  # Truncate long text
                            "reactions": reactions_count,
                            "comments": comments_count,
                            "shares": shares_count,
                            "mentions": post_text.count('@')  # Simple mention count
                        })
                        
                        posts_collected += 1
                        print(f"Collected post {posts_collected}/{MAX_POSTS}")
                        
                        if posts_collected >= MAX_POSTS:
                            break
                            
                    except Exception as e:
                        print(f"Error processing post: {str(e)[:100]}")
                        continue
                        
            return data
            
        except WebDriverException as e:
            print(f"Attempt {attempt + 1} failed: {str(e)[:100]}")
            if attempt == MAX_RETRIES - 1:
                return []
            time.sleep(BETWEEN_PAGE_DELAY)  # Wait before retrying
            continue

def main():
    driver = None
    try:
        print("Starting Facebook scraper...")
        driver = setup_driver()
        all_data = []
        
        for page_name, page_url in PAGES.items():
            page_data = scrape_page(driver, page_name, page_url)
            all_data.extend(page_data)
            
            if page_name != list(PAGES.keys())[-1]:  # If not last page
                print(f"Waiting {BETWEEN_PAGE_DELAY} seconds before next page...")
                time.sleep(BETWEEN_PAGE_DELAY)
            
        # Save results
        if all_data:
            df = pd.DataFrame(all_data)
            output_file = "facebook_engagement_data.csv"
            df.to_csv(output_file, index=False)
            print(f"\nSuccess! Data saved to {output_file}")
            print(f"Collected {len(all_data)} posts total")
        else:
            print("\nNo data was collected")
            
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
    finally:
        if driver:
            driver.quit()
        print("Scraping completed")

if __name__ == "__main__":
    main()