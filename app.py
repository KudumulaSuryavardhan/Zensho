from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from database.database import get_db_connection, init_db

from functools import wraps
from pathlib import Path
import os


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = "zensho_secret_key_2026"


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)


# =========================================================
# ALLOWED IMAGE FILES
# =========================================================

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp"
}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

init_db()

def create_default_admin():
    conn = get_db_connection()

    admin_email = "kudumulasuryavardhan@gmail.com"
    admin_password = "Sai Surya"

    existing_admin = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (admin_email,)
    ).fetchone()

    if existing_admin is None:

        password_hash = generate_password_hash(admin_password)

        conn.execute(
            """
            INSERT INTO users
            (name, email, password, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                "Zensho Admin",
                admin_email,
                password_hash,
                "admin"
            )
        )

        conn.commit()

        print("Default admin account created.")

    else:

        conn.execute(
            """
            UPDATE users
            SET role = 'admin'
            WHERE email = ?
            """,
            (admin_email,)
        )

        conn.commit()

        print("Default admin account already exists.")

    conn.close()


# =========================================================
# CART COUNT
# =========================================================

@app.context_processor
def inject_cart_count():

    cart_count = 0

    if "user_id" in session:

        conn = get_db_connection()

        result = conn.execute(
            """
            SELECT COALESCE(SUM(quantity), 0) AS count
            FROM cart
            WHERE user_id = ?
            """,
            (session["user_id"],)
        ).fetchone()

        conn.close()

        cart_count = result["count"]

    return {
        "cart_count": cart_count
    }


# =========================================================
# ADMIN LOGIN CHECK
# =========================================================

def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("home"))

        return function(*args, **kwargs)

    return wrapper


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    conn = get_db_connection()

    products = conn.execute(
        """
        SELECT *
        FROM products
        ORDER BY id DESC
        LIMIT 20
        """
    ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        products=products
    )


# =========================================================
# PRODUCTS
# =========================================================

@app.route("/products")
def products():

    search = request.args.get("search", "").strip()

    category = request.args.get("category", "").strip()

    conn = get_db_connection()

    query = """
        SELECT *
        FROM products
        WHERE 1 = 1
    """

    params = []

    if search:

        query += """
            AND (
                name LIKE ?
                OR description LIKE ?
                OR category LIKE ?
            )
        """

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value,
            search_value
        ])

    if category:

        query += " AND category = ?"

        params.append(category)

    query += " ORDER BY id DESC"

    products_list = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()

    return render_template(
        "products.html",
        products=products_list
    )


# =========================================================
# PRODUCT DETAILS
# =========================================================

@app.route("/product/<int:product_id>")
def product_details(product_id):

    conn = get_db_connection()

    product = conn.execute(
        """
        SELECT *
        FROM products
        WHERE id = ?
        """,
        (product_id,)
    ).fetchone()

    conn.close()

    if product is None:

        flash("Product not found.", "error")

        return redirect(url_for("products"))

    return render_template(
        "product_details.html",
        product=product
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        email = request.form.get("email", "").strip().lower()

        password = request.form.get("password", "")

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not name or not email or not password:

            flash(
                "Please fill all required fields.",
                "error"
            )

            return redirect(url_for("register"))

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return redirect(url_for("register"))

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "error"
            )

            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        conn = get_db_connection()

        try:

            conn.execute(
                """
                INSERT INTO users
                (name, email, password, role)
                VALUES (?, ?, ?, ?)
                """,
                (
                    name,
                    email,
                    password_hash,
                    "customer"
                )
            )

            conn.commit()

            flash(
                "Registration successful. Please login.",
                "success"
            )

        except Exception:

            flash(
                "Email already exists.",
                "error"
            )

        finally:

            conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        conn = get_db_connection()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["user_name"] = user["name"]

            session["role"] = user["role"]

            flash(
                f"Welcome, {user['name']}!",
                "success"
            )

            if user["role"] == "admin":

                return redirect(
                    url_for("admin_dashboard")
                )

            return redirect(url_for("home"))

        flash(
            "Invalid email or password.",
            "error"
        )

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(url_for("home"))


# =========================================================
# ADD TO CART
# =========================================================

@app.route(
    "/cart/add/<int:product_id>",
    methods=["POST"]
)
def add_to_cart(product_id):

    if "user_id" not in session:

        flash(
            "Please login to add products to cart.",
            "error"
        )

        return redirect(url_for("login"))

    quantity = request.form.get(
        "quantity",
        1,
        type=int
    )

    if quantity < 1:
        quantity = 1

    conn = get_db_connection()

    product = conn.execute(
        """
        SELECT *
        FROM products
        WHERE id = ?
        """,
        (product_id,)
    ).fetchone()

    if product is None:

        conn.close()

        flash(
            "Product not found.",
            "error"
        )

        return redirect(url_for("products"))

    if product["stock"] <= 0:

        conn.close()

        flash(
            "Product is out of stock.",
            "error"
        )

        return redirect(
            url_for(
                "product_details",
                product_id=product_id
            )
        )

    existing = conn.execute(
        """
        SELECT *
        FROM cart
        WHERE user_id = ?
        AND product_id = ?
        """,
        (
            session["user_id"],
            product_id
        )
    ).fetchone()

    if existing:

        new_quantity = existing["quantity"] + quantity

        if new_quantity > product["stock"]:

            new_quantity = product["stock"]

        conn.execute(
            """
            UPDATE cart
            SET quantity = ?
            WHERE id = ?
            """,
            (
                new_quantity,
                existing["id"]
            )
        )

    else:

        if quantity > product["stock"]:
            quantity = product["stock"]

        conn.execute(
            """
            INSERT INTO cart
            (user_id, product_id, quantity)
            VALUES (?, ?, ?)
            """,
            (
                session["user_id"],
                product_id,
                quantity
            )
        )

    conn.commit()

    conn.close()

    flash(
        "Product added to cart.",
        "success"
    )

    return redirect(url_for("cart"))


# =========================================================
# CART
# =========================================================

@app.route("/cart")
def cart():

    if "user_id" not in session:

        flash(
            "Please login to view your cart.",
            "error"
        )

        return redirect(url_for("login"))

    conn = get_db_connection()

    cart_items = conn.execute(
        """
        SELECT
            cart.id,
            cart.product_id,
            cart.quantity,
            products.name,
            products.category,
            products.price,
            products.image,
            products.stock
        FROM cart
        JOIN products
        ON cart.product_id = products.id
        WHERE cart.user_id = ?
        ORDER BY cart.id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    total = sum(
        item["price"] * item["quantity"]
        for item in cart_items
    )

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )


# =========================================================
# UPDATE CART
# =========================================================

@app.route(
    "/cart/update/<int:product_id>",
    methods=["POST"]
)
def update_cart(product_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    action = request.form.get("action")

    conn = get_db_connection()

    item = conn.execute(
        """
        SELECT
            cart.*,
            products.stock
        FROM cart
        JOIN products
        ON cart.product_id = products.id
        WHERE cart.user_id = ?
        AND cart.product_id = ?
        """,
        (
            session["user_id"],
            product_id
        )
    ).fetchone()

    if item is None:

        conn.close()

        return redirect(url_for("cart"))

    quantity = item["quantity"]

    if action == "increase":

        if quantity < item["stock"]:
            quantity += 1

    elif action == "decrease":

        quantity -= 1

    if quantity <= 0:

        conn.execute(
            """
            DELETE FROM cart
            WHERE user_id = ?
            AND product_id = ?
            """,
            (
                session["user_id"],
                product_id
            )
        )

    else:

        conn.execute(
            """
            UPDATE cart
            SET quantity = ?
            WHERE user_id = ?
            AND product_id = ?
            """,
            (
                quantity,
                session["user_id"],
                product_id
            )
        )

    conn.commit()

    conn.close()

    return redirect(url_for("cart"))


# =========================================================
# REMOVE FROM CART
# =========================================================

@app.route(
    "/cart/remove/<int:product_id>",
    methods=["POST"]
)
def remove_from_cart(product_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    conn.execute(
        """
        DELETE FROM cart
        WHERE user_id = ?
        AND product_id = ?
        """,
        (
            session["user_id"],
            product_id
        )
    )

    conn.commit()

    conn.close()

    flash(
        "Product removed from cart.",
        "success"
    )

    return redirect(url_for("cart"))


# =========================================================
# CHECKOUT
# =========================================================

@app.route(
    "/checkout",
    methods=["GET", "POST"]
)
def checkout():

    if "user_id" not in session:

        flash(
            "Please login before checkout.",
            "error"
        )

        return redirect(url_for("login"))

    conn = get_db_connection()

    cart_items = conn.execute(
        """
        SELECT
            cart.product_id,
            cart.quantity,
            products.name,
            products.price,
            products.stock,
            products.image
        FROM cart
        JOIN products
        ON cart.product_id = products.id
        WHERE cart.user_id = ?
        """,
        (session["user_id"],)
    ).fetchall()

    if not cart_items:

        conn.close()

        flash(
            "Your cart is empty.",
            "error"
        )

        return redirect(url_for("products"))

    subtotal = sum(
        item["price"] * item["quantity"]
        for item in cart_items
    )

    delivery_charge = 0 if subtotal >= 499 else 40

    total = subtotal + delivery_charge

    if request.method == "POST":

        address = request.form.get(
            "address",
            ""
        ).strip()

        city = request.form.get(
            "city",
            ""
        ).strip()

        pincode = request.form.get(
            "pincode",
            ""
        ).strip()

        payment_method = request.form.get(
            "payment_method",
            ""
        )

        if not address or not city or not pincode:

            conn.close()

            flash(
                "Please enter complete delivery details.",
                "error"
            )

            return redirect(url_for("checkout"))

        if payment_method not in [
            "UPI",
            "Card",
            "Wallet",
            "Cash on Delivery"
        ]:

            conn.close()

            flash(
                "Please select a valid payment method.",
                "error"
            )

            return redirect(url_for("checkout"))

        full_address = (
            address
            + ", "
            + city
            + " - "
            + pincode
        )

        # Check stock again
        for item in cart_items:

            if item["quantity"] > item["stock"]:

                conn.close()

                flash(
                    f"Not enough stock for {item['name']}.",
                    "error"
                )

                return redirect(url_for("cart"))

        # Create order
        cursor = conn.execute(
            """
            INSERT INTO orders
            (
                user_id,
                total_amount,
                status,
                address,
                payment_method
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                total,
                "Processing",
                full_address,
                payment_method
            )
        )

        order_id = cursor.lastrowid

        # Create order items
        for item in cart_items:

            conn.execute(
                """
                INSERT INTO order_items
                (
                    order_id,
                    product_id,
                    quantity,
                    price
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    order_id,
                    item["product_id"],
                    item["quantity"],
                    item["price"]
                )
            )

            # Reduce stock
            conn.execute(
                """
                UPDATE products
                SET stock = stock - ?
                WHERE id = ?
                """,
                (
                    item["quantity"],
                    item["product_id"]
                )
            )

        # Empty cart
        conn.execute(
            """
            DELETE FROM cart
            WHERE user_id = ?
            """,
            (session["user_id"],)
        )

        conn.commit()

        conn.close()

        return render_template(
            "order_success.html",
            order_id=order_id,
            total=total
        )

    conn.close()

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        total=subtotal
    )


# =========================================================
# CUSTOMER ORDERS
# =========================================================

@app.route("/orders")
def orders():

    if "user_id" not in session:

        flash(
            "Please login to view your orders.",
            "error"
        )

        return redirect(url_for("login"))

    conn = get_db_connection()

    order_rows = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    orders_list = []

    for order in order_rows:

        items = conn.execute(
            """
            SELECT
                order_items.*,
                products.name,
                products.image
            FROM order_items
            JOIN products
            ON order_items.product_id = products.id
            WHERE order_items.order_id = ?
            """,
            (order["id"],)
        ).fetchall()

        order_data = dict(order)

        order_data["items"] = items

        orders_list.append(order_data)

    conn.close()

    return render_template(
        "orders.html",
        orders=orders_list
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
@admin_required
def admin_dashboard():

    conn = get_db_connection()

    total_products = conn.execute(
        "SELECT COUNT(*) AS count FROM products"
    ).fetchone()["count"]

    total_users = conn.execute(
        "SELECT COUNT(*) AS count FROM users"
    ).fetchone()["count"]

    total_orders = conn.execute(
        "SELECT COUNT(*) AS count FROM orders"
    ).fetchone()["count"]

    total_sales = conn.execute(
        """
        SELECT COALESCE(SUM(total_amount), 0) AS total
        FROM orders
        WHERE status != 'Cancelled'
        """
    ).fetchone()["total"]

    recent_orders = conn.execute(
        """
        SELECT
            orders.*,
            users.name,
            users.email
        FROM orders
        JOIN users
        ON orders.user_id = users.id
        ORDER BY orders.id DESC
        LIMIT 10
        """
    ).fetchall()

    low_stock_products = conn.execute(
        """
        SELECT *
        FROM products
        WHERE stock <= 5
        ORDER BY stock ASC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "admin/dashboard.html",
        total_products=total_products,
        total_users=total_users,
        total_orders=total_orders,
        total_sales=total_sales,
        recent_orders=recent_orders,
        low_stock_products=low_stock_products
    )


# =========================================================
# ADMIN PRODUCTS
# =========================================================

@app.route("/admin/products")
@admin_required
def admin_products():

    conn = get_db_connection()

    products_list = conn.execute(
        """
        SELECT *
        FROM products
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "admin/products.html",
        products=products_list
    )


# =========================================================
# ADD PRODUCT
# =========================================================

@app.route(
    "/admin/products/add",
    methods=["GET", "POST"]
)
@admin_required
def add_product():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        try:

            price = float(
                request.form.get(
                    "price",
                    0
                )
            )

            stock = int(
                request.form.get(
                    "stock",
                    0
                )
            )

        except ValueError:

            flash(
                "Price or stock is invalid.",
                "error"
            )

            return redirect(url_for("add_product"))

        image_name = None

        image = request.files.get("image")

        if image and image.filename:

            if not allowed_file(image.filename):

                flash(
                    "Invalid image format.",
                    "error"
                )

                return redirect(
                    url_for("add_product")
                )

            filename = secure_filename(
                image.filename
            )

            image_name = filename

            image.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

        if not name or not category:

            flash(
                "Product name and category are required.",
                "error"
            )

            return redirect(
                url_for("add_product")
            )

        conn = get_db_connection()

        conn.execute(
            """
            INSERT INTO products
            (
                name,
                description,
                price,
                category,
                image,
                stock
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                description,
                price,
                category,
                image_name,
                stock
            )
        )

        conn.commit()

        conn.close()

        flash(
            "Product added successfully.",
            "success"
        )

        return redirect(
            url_for("admin_products")
        )

    return render_template(
        "admin/add_product.html"
    )


# =========================================================
# EDIT PRODUCT
# =========================================================

@app.route(
    "/admin/products/edit/<int:product_id>",
    methods=["GET", "POST"]
)
@admin_required
def edit_product(product_id):

    conn = get_db_connection()

    product = conn.execute(
        """
        SELECT *
        FROM products
        WHERE id = ?
        """,
        (product_id,)
    ).fetchone()

    if product is None:

        conn.close()

        flash(
            "Product not found.",
            "error"
        )

        return redirect(
            url_for("admin_products")
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        try:

            price = float(
                request.form.get(
                    "price",
                    0
                )
            )

            stock = int(
                request.form.get(
                    "stock",
                    0
                )
            )

        except ValueError:

            conn.close()

            flash(
                "Invalid price or stock.",
                "error"
            )

            return redirect(
                url_for(
                    "edit_product",
                    product_id=product_id
                )
            )

        image_name = product["image"]

        image = request.files.get("image")

        if image and image.filename:

            if not allowed_file(image.filename):

                conn.close()

                flash(
                    "Invalid image format.",
                    "error"
                )

                return redirect(
                    url_for(
                        "edit_product",
                        product_id=product_id
                    )
                )

            filename = secure_filename(
                image.filename
            )

            image_name = filename

            image.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

        conn.execute(
            """
            UPDATE products
            SET
                name = ?,
                description = ?,
                price = ?,
                category = ?,
                image = ?,
                stock = ?
            WHERE id = ?
            """,
            (
                name,
                description,
                price,
                category,
                image_name,
                stock,
                product_id
            )
        )

        conn.commit()

        conn.close()

        flash(
            "Product updated successfully.",
            "success"
        )

        return redirect(
            url_for("admin_products")
        )

    conn.close()

    return render_template(
        "admin/edit_product.html",
        product=product
    )


# =========================================================
# DELETE PRODUCT
# =========================================================

@app.route(
    "/admin/products/delete/<int:product_id>",
    methods=["POST"]
)
@admin_required
def delete_product(product_id):

    conn = get_db_connection()

    product = conn.execute(
        """
        SELECT *
        FROM products
        WHERE id = ?
        """,
        (product_id,)
    ).fetchone()

    if product:

        conn.execute(
            """
            DELETE FROM products
            WHERE id = ?
            """,
            (product_id,)
        )

        conn.commit()

    conn.close()

    flash(
        "Product deleted.",
        "success"
    )

    return redirect(
        url_for("admin_products")
    )


# =========================================================
# ADMIN ORDERS
# =========================================================

@app.route("/admin/orders")
@admin_required
def admin_orders():

    conn = get_db_connection()

    orders_list = conn.execute(
        """
        SELECT
            orders.*,
            users.name,
            users.email
        FROM orders
        JOIN users
        ON orders.user_id = users.id
        ORDER BY orders.id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "admin/orders.html",
        orders=orders_list
    )


# =========================================================
# ADMIN ORDER DETAILS
# =========================================================

@app.route("/admin/orders/<int:order_id>")
@admin_required
def admin_order_detail(order_id):

    conn = get_db_connection()

    order = conn.execute(
        """
        SELECT
            orders.*,
            users.name,
            users.email
        FROM orders
        JOIN users
        ON orders.user_id = users.id
        WHERE orders.id = ?
        """,
        (order_id,)
    ).fetchone()

    if order is None:

        conn.close()

        flash(
            "Order not found.",
            "error"
        )

        return redirect(
            url_for("admin_orders")
        )

    items = conn.execute(
        """
        SELECT
            order_items.*,
            products.name,
            products.image
        FROM order_items
        JOIN products
        ON order_items.product_id = products.id
        WHERE order_items.order_id = ?
        """,
        (order_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "admin/order_detail.html",
        order=order,
        items=items
    )


# =========================================================
# UPDATE ORDER STATUS
# =========================================================

@app.route(
    "/admin/orders/<int:order_id>/status",
    methods=["POST"]
)
@admin_required
def update_order_status(order_id):

    status = request.form.get(
        "status",
        ""
    )

    allowed_statuses = [
        "Processing",
        "Packed",
        "Shipped",
        "Delivered",
        "Cancelled"
    ]

    if status not in allowed_statuses:

        flash(
            "Invalid order status.",
            "error"
        )

        return redirect(
            url_for("admin_orders")
        )

    conn = get_db_connection()

    conn.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            order_id
        )
    )

    conn.commit()

    conn.close()

    flash(
        "Order status updated.",
        "success"
    )

    return redirect(
        url_for("admin_orders")
    )


# =========================================================
# ADMIN USERS
# =========================================================

@app.route("/admin/users")
@admin_required
def admin_users():

    conn = get_db_connection()

    users = conn.execute(
        """
        SELECT *
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "admin/users.html",
        users=users
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )