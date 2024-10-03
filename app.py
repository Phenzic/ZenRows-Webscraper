
from zenrows import ZenRowsClient 
import re
import json
import time
import csv
from dotenv import load_dotenv
import os
import requests

load_dotenv()

def parse_products(response_json):
    try:
        data = json.loads(response_json)
        md_content = data.get('md', '')
        pattern = r'\[!\[([^\]]+)\]\(([^\)]+)\)\\*\n([^\\\n]+)\\*\n\\*\n\$(\d+)\]\(([^\)]+)\)'
        matches = re.findall(pattern, md_content)
        
        products = []
        for match in matches:
            product = {
                'name': match[0],
                'image_link': match[1],
                'price': int(match[3]),
                'product_url': match[4]
            }
            products.append(product)
        
        return products
    except json.JSONDecodeError:
        print("Error: Unable to parse JSON response")
        print("Response content:", response_json[:500])
        return []
    except Exception as e:
        print(f"Error parsing products: {str(e)}")
        return []

def save_to_csv(products, filename='products.csv'):
    """Save product data to a CSV file."""
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['name', 'image_link', 'price', 'product_url'])
        writer.writeheader()
        for product in products:
            writer.writerow(product)
    print(f"Saved {len(products)} products to {filename}.")

def extract_product_details(product_url):
    """Extract product description and SKU from a product page."""
    try:
        response = requests.get(product_url)
        response.raise_for_status()  # Check for HTTP errors
        product_data = json.loads(response.text)

        # Example extraction logic for description and SKU; update according to the actual structure
        description = product_data.get('description', 'No description found')
        sku = product_data.get('sku', 'No SKU found')

        return description, sku
    except Exception as e:
        print(f"Error fetching product details from {product_url}: {str(e)}")
        return None, None

client = ZenRowsClient(os.getenv("API_KEY"))

# URL of the page you want to scrape
url = "https://www.scrapingcourse.com/button-click"

# Set up initial parameters for JavaScript rendering and interaction
base_params = {
    "js_render": "true",
    "json_response": "true",
    "premium_proxy": "true",
    "markdown_response": "true"
}

all_products = []
page = 1
max_products = 50  # Set this to the number of products you want to retrieve

while len(all_products) < max_products:
    print(f"Scraping page {page}...")
    
    # Update parameters for each request
    params = base_params.copy()
    js_instructions = [{"click": "#load-more-btn"} for _ in range(page)]
    js_instructions.append({"wait": 5000})
    params["js_instructions"] = json.dumps(js_instructions)
    
    try:
        # Send the GET request to ZenRows
        response = client.get(url, params=params)
        
        # Parse the response JSON
        new_products = parse_products(response.text)
        
        if not new_products:
            print("No more products found. Stopping.")
            break
        
        all_products.extend(new_products)
        print(f"Found {len(new_products)} products on this page.")
        print(f"Total products so far: {len(all_products)}")
        
        page += 1
        
        # Add a delay to avoid overwhelming the server
        time.sleep(2)
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        break

# Save all products to a CSV file
save_to_csv(all_products)

# Identify the 5 highest-priced products
highest_priced_products = sorted(all_products, key=lambda x: x['price'], reverse=True)[:5]

print("\nFive highest-priced products:")
for product in highest_priced_products:
    print(product)

# Visit each product page and extract details
for product in highest_priced_products:
    description, sku = extract_product_details(product['product_url'])
    print(f"Product: {product['name']}, Description: {description}, SKU: {sku}")

# Calculate the total price of all products
total_sum = sum(product['price'] for product in all_products)

print("\nAll products:")
for product in all_products:
    print(product)

# Print the total sum of the product prices
print(f"\nTotal number of products: {len(all_products)}")
print(f"Total sum of product prices: ${total_sum}")
