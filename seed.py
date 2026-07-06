import sqlite3
import random

conn = sqlite3.connect('smartcart.db')
cursor = conn.cursor()

electronics = [
    ("Smartphone X", "Latest 5G smartphone with advanced camera.", "p-1.png"),
    ("Laptop Pro", "High performance laptop for professionals.", "p-1.png"),
    ("Wireless Earbuds", "Noise-cancelling wireless earbuds.", "p-1.png"),
    ("Smartwatch Series 5", "Health and fitness tracking smartwatch.", "p-1.png"),
    ("4K Smart TV", "Ultra HD smart TV with vibrant colors.", "p-1.png"),
    ("Gaming Console", "Next-gen gaming console with 1TB storage.", "p-1.png"),
    ("Bluetooth Speaker", "Portable waterproof bluetooth speaker.", "p-1.png"),
    ("Digital Camera", "Mirrorless digital camera with 4K video.", "p-1.png"),
    ("Tablet Air", "Lightweight tablet with stunning display.", "p-1.png"),
    ("Wireless Mouse", "Ergonomic wireless mouse for productivity.", "p-1.png")
]

men_clothing = [
    ("Classic Polo T-Shirt", "Comfortable cotton polo t-shirt.", "shirt.webp"),
    ("Slim Fit Jeans", "Stylish slim fit denim jeans.", "shirt.webp"),
    ("Casual Shirt", "Checkered casual shirt for everyday wear.", "shirt.webp"),
    ("Formal Trousers", "Elegant formal trousers for office.", "shirt.webp"),
    ("Winter Jacket", "Warm and cozy winter jacket.", "shirt.webp"),
    ("Running Shoes", "Lightweight running shoes.", "shirt.webp"),
    ("Leather Wallet", "Premium genuine leather wallet.", "shirt.webp"),
    ("Aviator Sunglasses", "Classic aviator sunglasses with UV protection.", "shirt.webp"),
    ("Sports Watch", "Durable sports watch with stopwatch.", "shirt.webp"),
    ("Cotton Socks Set", "Pack of 5 breathable cotton socks.", "shirt.webp")
]

women_clothing = [
    ("Floral Summer Dress", "Beautiful floral print summer dress.", "shirt.webp"),
    ("Skinny Jeans", "High-waisted skinny denim jeans.", "shirt.webp"),
    ("Silk Blouse", "Elegant silk blouse for evening wear.", "shirt.webp"),
    ("Pleated Skirt", "Stylish pleated midi skirt.", "shirt.webp"),
    ("Trench Coat", "Classic beige trench coat.", "shirt.webp"),
    ("Heels", "Comfortable block heels for parties.", "shirt.webp"),
    ("Leather Handbag", "Spacious genuine leather handbag.", "shirt.webp"),
    ("Cat-eye Sunglasses", "Trendy cat-eye sunglasses.", "shirt.webp"),
    ("Gold Plated Necklace", "Elegant gold plated pendant necklace.", "shirt.webp"),
    ("Scarf", "Soft woven scarf for winter.", "shirt.webp")
]

def insert_products(category, products_list):
    for name, desc, img in products_list:
        price = round(random.uniform(900.0, 10000.0), 2)
        cursor.execute(
            "INSERT INTO products (name, description, category, price, image_name) VALUES (?, ?, ?, ?, ?)",
            (name, desc, category, price, img)
        )

insert_products("Electronics", electronics)
insert_products("Men", men_clothing)
insert_products("Women", women_clothing)

conn.commit()
cursor.close()
conn.close()

print("Successfully inserted 30 dummy products!")
