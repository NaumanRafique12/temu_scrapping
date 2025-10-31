"""
Temu Scraper - Automated "See More" Button Clicker
===================================================
This script connects to an existing Chrome instance and automatically
clicks the "See more" button a specified number of times, then saves
the HTML for later parsing with BeautifulSoup.

Usage:
1. Run temu.py first to launch Chrome with remote debugging
2. Manually log in to Temu if required
3. Run this script to automate the clicking process
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# ============================================================================
# CONFIGURATION - Modify these values as needed
# ============================================================================

# Target URL for scraping
TEMU_URL = "https://www.temu.com/pk-en/home-decor-products-o3-751.html?opt_level=2&title=Home%20Decor%20Products&_x_enter_scene_type=cate_tab&leaf_type=bro&show_search_type=3&opt1_id=-13"

# Number of times to click "See more" button
NUM_CLICKS = 5

# Output filename for saved HTML
SAVE_FILENAME = "temu_scraped.html"

# Chrome remote debugging port
DEBUG_PORT = 9222

# Wait times (in seconds)
SCROLL_WAIT = 30  # Wait time after scrolling
AFTER_CLICK_WAIT = 30  # Wait time after clicking "See more" for content to load
BUTTON_TIMEOUT = 10

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def smooth_scroll_to_bottom(driver):
    """
    Scrolls the page to the bottom smoothly to make "See more" button visible.
    """
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(0.5)


def wait_for_content_load(driver, wait_time=3):
    """
    Waits for content to load after clicking "See more".
    """
    time.sleep(wait_time)


def get_page_stats(driver):
    """
    Gets statistics about the current page (for debugging).
    """
    try:
        stats = driver.execute_script("""
            return {
                productCount: document.querySelectorAll('[data-goods-id]').length,
                pageHeight: document.body.scrollHeight,
                hasReactRoot: !!document.getElementById('__next') || !!document.querySelector('[data-reactroot]')
            };
        """)
        return stats
    except:
        return {"productCount": 0, "pageHeight": 0, "hasReactRoot": False}


def click_see_more_button(driver, timeout=10):
    """
    Attempts to find and click the "See more" button using multiple XPath selectors.
    
    Args:
        driver: Selenium WebDriver instance
        timeout: Maximum time to wait for button (in seconds)
    
    Returns:
        True if button was clicked successfully, False otherwise
    """
    # List of XPath selectors to try (in priority order)
    xpaths = [
        "//div[@role='button' and @aria-label='See more items']",
        "//div[@role='button' and contains(., 'See more')]",
        "//div[contains(@class, '_2ugbvrpI') and @aria-label='See more items']",
        "//button[contains(., 'See more')]",
        "//div[@role='button' and contains(text(), 'See more')]",
        "//button[contains(text(), 'See more')]",
        "//*[contains(text(), 'See more')]",
        "//*[@aria-label='See more items']"
    ]
    
    # First, try to find any button using JavaScript
    print("  → Searching for button using JavaScript...")
    js_buttons = driver.execute_script("""
        var buttons = [];
        var allElements = document.querySelectorAll('*');
        for (var i = 0; i < allElements.length; i++) {
            var el = allElements[i];
            var text = el.textContent || el.innerText || '';
            if (text.toLowerCase().includes('see more') && el.offsetParent !== null) {
                buttons.push({
                    tag: el.tagName,
                    class: el.className,
                    text: text.substring(0, 50),
                    role: el.getAttribute('role'),
                    ariaLabel: el.getAttribute('aria-label')
                });
            }
        }
        return buttons;
    """)
    
    if js_buttons:
        print(f"  → Found {len(js_buttons)} potential 'See more' element(s):")
        for btn in js_buttons[:3]:  # Show first 3
            print(f"     • Tag: {btn['tag']}, Class: {btn['class'][:30] if btn['class'] else 'N/A'}")
    
    for xpath in xpaths:
        try:
            # Try to find the button with a short timeout
            button = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            
            # Check if button is visible
            if not button.is_displayed():
                print(f"  → Button found but not visible with XPath: {xpath[:40]}...")
                continue
            
            # Scroll button into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(1)
            
            # Try to click the button
            try:
                button.click()
                print(f"  ✓ Button clicked using XPath: {xpath[:50]}...")
                return True
            except ElementClickInterceptedException:
                # If normal click fails, try JavaScript click
                driver.execute_script("arguments[0].click();", button)
                print(f"  ✓ Button clicked (JavaScript) using XPath: {xpath[:50]}...")
                return True
                
        except (TimeoutException, NoSuchElementException):
            # This XPath didn't work, try next one
            continue
    
    # If none of the XPaths worked, return False
    print("  ✗ 'See more' button not found with any selector")
    print("  → This might mean:")
    print("     • All products are already loaded")
    print("     • The page uses infinite scroll instead of a button")
    print("     • The button has a different structure")
    return False


def close_popups_and_banners(driver):
    """
    Attempts to close any popup banners, cookie notices, etc.
    """
    # Common selectors for close buttons
    close_selectors = [
        "//button[contains(text(), 'Accept')]",
        "//button[contains(text(), 'Close')]",
        "//div[@role='button' and contains(@aria-label, 'close')]",
        "//button[@aria-label='Close']"
    ]
    
    for selector in close_selectors:
        try:
            close_btn = driver.find_element(By.XPATH, selector)
            close_btn.click()
            print("  ✓ Closed popup/banner")
            time.sleep(1)
        except:
            pass


# ============================================================================
# MAIN SCRAPING LOGIC
# ============================================================================

def main():
    """
    Main function that orchestrates the scraping process.
    """
    print("=" * 70)
    print("Temu Scraper - Automated 'See More' Clicker")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  • Target URL: {TEMU_URL}")
    print(f"  • Number of clicks: {NUM_CLICKS}")
    print(f"  • Output file: {SAVE_FILENAME}")
    print(f"  • Debug port: {DEBUG_PORT}")
    print("\n" + "=" * 70 + "\n")
    
    # Step 1: Connect to existing Chrome instance
    print("Step 1: Connecting to Chrome debugging session...")
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.debugger_address = f"localhost:{DEBUG_PORT}"
        
        driver = webdriver.Chrome(options=chrome_options)
        print("  ✓ Successfully connected to Chrome\n")
    except Exception as e:
        print(f"  ✗ Error connecting to Chrome: {e}")
        print("\n  Make sure you've run 'python temu.py' first!")
        return
    
    # Step 2: Navigate to Temu URL
    print("Step 2: Navigating to Temu page...")
    try:
        driver.get(TEMU_URL)
        print("  → Waiting for React content to load...")
        time.sleep(10)  # Initial wait for page to start rendering
        
        # Wait for React root to be populated with content
        try:
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.querySelectorAll('[data-goods-id]').length > 0")
            )
            print("  ✓ Products loaded successfully")
        except TimeoutException:
            print("  ⚠️ Timeout waiting for products, but continuing...")
        
        print("  ✓ Page loaded successfully\n")
    except Exception as e:
        print(f"  ✗ Error loading page: {e}\n")
        driver.quit()
        return
    
    # Step 3: Close any popups/banners
    print("Step 3: Closing popups and banners...")
    close_popups_and_banners(driver)
    time.sleep(1)
    print("  ✓ Popups handled\n")
    
    # Step 4: Main clicking loop
    print(f"Step 4: Clicking 'See more' button {NUM_CLICKS} times...")
    print("-" * 70)
    
    successful_clicks = 0
    failed_clicks = 0
    
    for i in range(1, NUM_CLICKS + 1):
        print(f"\nAttempt {i}/{NUM_CLICKS}:")
        
        # Show current page stats
        stats = get_page_stats(driver)
        print(f"  → Current products on page: {stats['productCount']}")
        print(f"  → Page height: {stats['pageHeight']}px")
        
        # Scroll to bottom
        print("  → Scrolling to bottom...")
        smooth_scroll_to_bottom(driver)
        time.sleep(SCROLL_WAIT)
        
        # Try to click the button
        print("  → Looking for 'See more' button...")
        clicked = click_see_more_button(driver, timeout=BUTTON_TIMEOUT)
        
        if clicked:
            successful_clicks += 1
            print(f"  → Waiting for content to load...")
            wait_for_content_load(driver, AFTER_CLICK_WAIT)
            
            # Show updated stats
            new_stats = get_page_stats(driver)
            print(f"  → New products on page: {new_stats['productCount']} (+{new_stats['productCount'] - stats['productCount']})")
            print(f"  ✓ Click {i}/{NUM_CLICKS} completed successfully")
        else:
            failed_clicks += 1
            print(f"  ✗ Click {i}/{NUM_CLICKS} failed (button not found)")
            print(f"  → This might mean we've reached the end of products")
            
            # Ask if we should continue or stop
            if i < NUM_CLICKS:
                print(f"  → Continuing to next attempt...")
                time.sleep(2)
    
    print("\n" + "-" * 70)
    print(f"\nClicking Summary:")
    print(f"  • Successful clicks: {successful_clicks}/{NUM_CLICKS}")
    print(f"  • Failed clicks: {failed_clicks}/{NUM_CLICKS}")
    
    # Final page stats
    final_stats = get_page_stats(driver)
    print(f"  • Final product count: {final_stats['productCount']}")
    print(f"  • Final page height: {final_stats['pageHeight']}px")
    
    # Step 5: Save HTML
    print(f"\nStep 5: Saving HTML to '{SAVE_FILENAME}'...")
    try:
        html_content = driver.page_source
        with open(SAVE_FILENAME, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"  ✓ HTML saved successfully ({len(html_content)} characters)")
        print(f"  ✓ File size: {len(html_content) / 1024:.2f} KB")
    except Exception as e:
        print(f"  ✗ Error saving HTML: {e}")
    
    # Final message
    print("\n" + "=" * 70)
    print("Scraping completed!")
    print(f"You can now parse '{SAVE_FILENAME}' with BeautifulSoup")
    print("=" * 70)
    
    # Keep browser open for inspection
    print("\n⚠️  Browser window kept open for inspection.")
    print("Close the browser manually when done.")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()

