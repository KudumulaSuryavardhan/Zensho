# Zensho - E-Commerce Website

Zensho is a web-based e-commerce application developed as an MCA academic project using Python Flask, SQLite, HTML, CSS, and JavaScript.

## Project Overview

Zensho provides an online shopping platform where customers can register, log in, browse products, search products, add products to their cart, place orders, view order history, track orders, and generate invoices.

The system also provides an administrator section for managing products, users, orders, inventory, and order tracking.

## Technologies Used

- Python
- Flask
- SQLite
- HTML5
- CSS3
- JavaScript
- Jinja2
- Werkzeug
- Gunicorn

## Main Features

### Customer

- User Registration
- User Login and Logout
- Product Browsing
- Product Search
- Category Filtering
- Product Details
- Add to Cart
- Update Cart Quantity
- Remove Products from Cart
- Checkout
- Multiple Demo Payment Methods
- Order Placement
- Order History
- Order Tracking
- Invoice
- Responsive User Interface

### Administrator

- Admin Login
- Admin Dashboard
- Product Management
- Add Products
- Edit Products
- Delete Products
- Product Image Upload
- Inventory Management
- User Management
- Order Management
- Order Status Updates
- Order Tracking
- Delivery Information

## Order Status

Orders can have the following statuses:

- Processing
- Packed
- Shipped
- Delivered
- Cancelled

## Project Structure

```text
Zensho/
│
├── app.py
├── database.db
├── requirements.txt
├── README.md
│
├── database/
│   └── database.py
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── products.html
│   ├── product_details.html
│   ├── login.html
│   ├── register.html
│   ├── cart.html
│   ├── checkout.html
│   ├── order_success.html
│   ├── orders.html
│   ├── track_order.html
│   ├── invoice.html
│   │
│   └── admin/
│       ├── base_admin.html
│       ├── dashboard.html
│       ├── products.html
│       ├── add_product.html
│       ├── edit_product.html
│       ├── orders.html
│       ├── order_detail.html
│       └── users.html
│
└── static/
    ├── css/
    │   └── style.css
    │
    ├── js/
    │   └── script.js
    │
    ├── images/
    │
    └── uploads/