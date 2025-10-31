"""
Final Working HTML to CSV Converter for Temu
============================================
Extracts product data from the rendered HTML structure.
"""

import csv
import re
import os
from bs4 import BeautifulSoup

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_HTML_FILE = "temu_scraped.html"
OUTPUT_CSV_FILE = "temu_products.csv"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_number(text):
    """Extract numeric value from text."""
    if not text:
        return None
    text = str(text).replace(',', '').replace(' ', '')
    if 'K+' in text or 'K' in text:
        match = re.search(r'(\d+\.?\d*)K', text)
        if match:
            return int(float(match.group(1)) * 1000)
    match = re.search(r'\d+\.?\d*', text)
    if match:
        return float(match.group())
    return None


def extract_price_from_text(text):
    """Extract price from text."""
    if not text:
        return None
    # Remove Rs., commas
    text = str(text).replace('Rs.', '').replace('Rs', '').replace(',', '').strip()
    match = re.search(r'\d+\.?\d*', text)
    if match:
        return float(match.group())
    return None


def parse_temu_html(html_file):
    """Parse Temu HTML and extract product data."""
    print(f"📖 Reading HTML file: {html_file}")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"   File size: {len(html_content) / 1024:.2f} KB\n")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    products = []
    
    # Find all product links
    product_links = soup.find_all('a', href=re.compile(r'/pk-en/.*\.html'))
    
    print(f"🔍 Found {len(product_links)} potential product links")
    
    # Filter to actual product pages (not navigation links)
    actual_products = []
    for link in product_links:
        href = link.get('href', '')
        # Skip navigation/category links
        if any(skip in href for skip in ['channel', 'home-kitchen', 'category', 'search']):
            continue
        # Must have product-like URL (long with product details)
        if len(href) > 30 and '-' in href:
            actual_products.append(link)
    
    print(f"   → Filtered to {len(actual_products)} actual product links\n")
    
    for idx, link in enumerate(actual_products, 1):
        try:
            href = link.get('href', '')
            title = link.get_text(strip=True)
            
            # Get the parent container that might have price/rating info
            parent = link.find_parent()
            while parent and parent.name != 'body':
                # Look for price information in parent
                text_content = parent.get_text()
                
                # Check if this parent has price info
                if 'Rs.' in text_content:
                    break
                parent = parent.find_parent()
            
            if not parent:
                parent = link.find_parent()
            
            # Extract all text from parent
            parent_text = parent.get_text() if parent else ''
            
            # Extract prices (look for Rs. followed by numbers)
            prices = re.findall(r'Rs\.?\s*([0-9,]+\.?\d*)', parent_text)
            prices = [extract_price_from_text(p) for p in prices if p]
            prices = [p for p in prices if p and p > 0]
            
            current_price = prices[0] if len(prices) >= 1 else None
            original_price = prices[1] if len(prices) >= 2 and prices[1] > prices[0] else None
            
            # Calculate discount
            discount = 0
            if original_price and current_price and original_price > current_price:
                discount = round(((original_price - current_price) / original_price) * 100, 2)
            
            # Extract sold count
            sold_match = re.search(r'(\d+\.?\d*K?\+?)\s*sold', parent_text, re.IGNORECASE)
            sold_count = 0
            if sold_match:
                sold_count = int(extract_number(sold_match.group(1)) or 0)
            
            # Extract rating (look for patterns like "4.7" near stars or "out of")
            rating = 0
            review_count = 0
            rating_match = re.search(r'([0-5]\.?\d*)\s*(?:out of|★)', parent_text)
            if not rating_match:
                # Look for standalone ratings
                rating_match = re.search(r'([4-5]\.\d+)', parent_text)
            
            if rating_match:
                rating = float(rating_match.group(1))
            
            # Extract review count
            review_match = re.search(r'(\d+)\s*(?:review|rating)', parent_text, re.IGNORECASE)
            if review_match:
                review_count = int(review_match.group(1))
            
            # Extract product ID from URL
            product_id = ''
            id_match = re.search(r'-g-(\d+)', href)
            if id_match:
                product_id = id_match.group(1)
            
            # Clean title (remove extra whitespace)
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Only add if has meaningful data
            if title and len(title) > 5:
                product_data = {
                    'product_id': product_id,
                    'title': title,
                    'current_price': current_price,
                    'original_price': original_price,
                    'discount_percent': discount,
                    'sold_count': sold_count,
                    'rating': rating,
                    'review_count': review_count,
                    'url': f"https://www.temu.com{href}" if not href.startswith('http') else href
                }
                
                products.append(product_data)
                
                # Show first 5 products
                if idx <= 5:
                    print(f"  Product {idx}:")
                    print(f"    Title: {title[:60]}...")
                    print(f"    Price: Rs.{current_price} (was Rs.{original_price})" if original_price else f"    Price: Rs.{current_price}")
                    print(f"    Sold: {sold_count}, Rating: {rating}/5 ({review_count} reviews)")
        
        except Exception as e:
            print(f"  ⚠️  Error parsing product {idx}: {e}")
            continue
    
    print(f"\n✅ Successfully parsed {len(products)} products")
    return products


def save_to_csv(products, output_file):
    """Save products to CSV."""
    print(f"\n💾 Saving data to CSV: {output_file}")
    
    if not products:
        print("  ⚠️ No products to save!")
        return
    
    fieldnames = [
        'Product ID',
        'Title',
        'Current Price (Rs.)',
        'Original Price (Rs.)',
        'Discount (%)',
        'Items Sold',
        'Rating (Stars)',
        'Review Count',
        'Product URL'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for product in products:
            writer.writerow({
                'Product ID': product['product_id'],
                'Title': product['title'],
                'Current Price (Rs.)': product['current_price'] or '',
                'Original Price (Rs.)': product['original_price'] or '',
                'Discount (%)': product['discount_percent'],
                'Items Sold': product['sold_count'],
                'Rating (Stars)': product['rating'],
                'Review Count': product['review_count'],
                'Product URL': product['url']
            })
    
    print(f"  ✓ Saved {len(products)} products to CSV")
    print(f"  ✓ File location: {os.path.abspath(output_file)}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("Temu HTML to CSV Converter (Final Version)")
    print("=" * 70)
    print(f"\nInput:  {INPUT_HTML_FILE}")
    print(f"Output: {OUTPUT_CSV_FILE}\n")
    print("=" * 70 + "\n")
    
    if not os.path.exists(INPUT_HTML_FILE):
        print(f"❌ Error: '{INPUT_HTML_FILE}' not found!")
        return
    
    # Parse HTML
    products = parse_temu_html(INPUT_HTML_FILE)
    
    # Save to CSV
    if products:
        save_to_csv(products, OUTPUT_CSV_FILE)
        
        # Statistics
        print("\n" + "=" * 70)
        print("📊 Summary Statistics:")
        print("=" * 70)
        print(f"  • Total products extracted: {len(products)}")
        
        prices = [p['current_price'] for p in products if p['current_price']]
        if prices:
            print(f"  • Price range: Rs.{min(prices):.2f} - Rs.{max(prices):.2f}")
            print(f"  • Average price: Rs.{sum(prices)/len(prices):.2f}")
        
        total_sold = sum(p['sold_count'] for p in products)
        print(f"  • Total items sold: {total_sold:,}")
        
        rated = [p for p in products if p['rating'] > 0]
        if rated:
            avg_rating = sum(p['rating'] for p in rated) / len(rated)
            print(f"  • Average rating: {avg_rating:.2f}/5")
        
        # Sample
        print("\n" + "=" * 70)
        print("Sample Products:")
        print("=" * 70)
        
        for idx, p in enumerate(products[:5], 1):
            print(f"\n{idx}. {p['title'][:65]}")
            if p['current_price']:
                orig = f" (was Rs.{p['original_price']:.2f})" if p['original_price'] else ""
                print(f"   💰 Rs.{p['current_price']:.2f}{orig}")
            if p['discount_percent'] > 0:
                print(f"   🏷️  {p['discount_percent']}% OFF")
            if p['sold_count'] > 0:
                print(f"   📦 {p['sold_count']:,} sold")
            if p['rating'] > 0:
                print(f"   ⭐ {p['rating']}/5 ({p['review_count']} reviews)")
        
        print("\n" + "=" * 70)
        print("✅ Conversion completed successfully!")
        print(f"📁 Open '{OUTPUT_CSV_FILE}' to view all data")
        print("=" * 70)
    else:
        print("\n❌ No products found!")


if __name__ == "__main__":
    main()

