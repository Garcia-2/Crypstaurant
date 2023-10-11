import os
import re
import random
import requests
import string
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, url_for, request, session, jsonify
from flask_session import Session
import paypalrestsdk
#from filters import zar
# from flask_mail import Mail, Message
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
#from validate_email_address import validate_email

from helpers import apology, login_required, usd, zar

CLIENT_ID = "AUR-za_IT1xufLFSYmHwl7plqkPWNTEWAtrDVr_bCVXol5wVvmelt2206h4c3Eqkplgt2nngtEw3qp2s"
CLIENT_SECRET = "ELuLVxcActXnFyq495gYlCwrM7Tel6W-Tkk18962IG5vPSEeQrkZZkGDk-bj78BZSM_Wu8zToPH-4NNn"

PAYPAL_CAPTURE_URL = "https://api.paypal.com/v2/checkout/orders/{order_id}/capture"

# Generate a random secret key
secret_key = os.urandom(24)

# Convert the bytes to a hexadecimal string
secret_key_hex = secret_key.hex()

# Configure application
app = Flask(__name__)
app.secret_key = secret_key_hex  # Set the secret key for Flask

paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" for production
    "client_id": "your_paypal_client_id",
    "client_secret": "your_paypal_client_secret"
})

# Custom filter
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters['zar'] = zar

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///restaurant.db")

"""
# Configure Flask-Mail for email sending
#app.config["MAIL_SERVER"] = "smtp.gmail.com"  # Use Gmail SMTP server
#app.config["MAIL_PORT"] = 587  # TLS port
#app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
app.config["MAIL_USERNAME"] = "my_email"  # Replace with your Gmail email
app.config["MAIL_PASSWORD"] = "my_email_password"  # Replace with your Gmail password
mail = Mail(app)
"""

# Function to generate a random verification token
def generate_verification_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():

    # Fetch product information from the database (replace with your actual query)
    products = db.execute("SELECT id, name, description, price, image_filename FROM products")

    return render_template("index.html", products=products)

# Registration route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Retrieve user inputALTER TABLE products
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        email = request.form.get("email")
        """
        # validate  email
        if not validate_email(email, verify=True):  # Verify the email format
            return apology("Invalid email address", 400)
        """

        # Check if the username, password, and email are provided
        if not username:
            return apology("must provide username", 400)

        if not password:
            return apology("must provide password", 400)

        # Check if the password meets the minimum length requirement (e.g., at least 8 characters)
        if len(password) < 8:
            return apology("password must be at least 8 characters", 400)

        # Check if the password meets complexity requirements
        if not re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$', password):
            return apology("password must contain at least one uppercase letter, one lowercase letter, one symbol, and one number", 400)

        # validate confirmation
        if not confirmation:
            return apology("Must confirm password", 400)

        if confirmation != password:
            return apology("Password confirmation must match password", 400)

        if not email:
            return apology("must provide email", 400)


        # Generate a password hash
        password_hash = generate_password_hash(password)

        # Check if the email is already registered

        existing_user = db.execute("SELECT * FROM users WHERE email = ?", email)
        if existing_user:
            return apology("email is already registered", 400)

        existing_username = db.execute("SELECT * FROM users WHERE username = ?", username)
        if existing_username:
            return apology("username is already registered", 400)

        # Generate a random verification token
        verification_token = generate_verification_token()

        # Store the verification token and user data in the database
        db.execute("INSERT INTO users (username, hash, email, verified, verification_token) VALUES (?, ?, ?, 0, ?)",
                    username, password_hash, email, verification_token)


        """
        # Send a verification email to the user
        msg = Message("Confirm Your Email", sender="garcia@moov.life", recipients=[email])
        verification_link = url_for('verify_email', token=verification_token, _external=True)
        msg.body = f"Click the following link to verify your email: {verification_link}"
        mail.send(msg)
        """

        flash("Registration successful!", "success")

        return redirect(url_for("login"))

    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Allow users to change their password"""
    if request.method == "POST":
        # Retrieve user input
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        # Retrieve the user's current password hash from the database
        user_id = session["user_id"]
        user_data = db.execute("SELECT hash FROM users WHERE id = ?", user_id)
        current_password_hash = user_data[0]["hash"]

        # Validate user input
        if not current_password or not new_password or not confirm_password:
            return apology("All fields must be filled out", 400)

        if new_password == current_password:
            return apology("New Password Can't Be The Same As the Old Password", 400)

        if not check_password_hash(current_password_hash, current_password):
            return apology("Current password is incorrect", 400)

        if len(new_password) < 8:
            return apology("password must be at least 8 characters", 400)

        # Check if the password meets complexity requirements
        if not re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$', new_password):
            return apology("password must contain at least one uppercase letter, one lowercase letter, one symbol, and one number", 400)

        if new_password != confirm_password:
            return apology("New passwords do not match", 400)

        # Generate a new password hash and update it in the database
        new_password_hash = generate_password_hash(new_password)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", new_password_hash, user_id)

        flash("Password changed successfully!", "success")
        return redirect("/")
    else:
        return render_template("change_password.html")



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Retrieve user ID from the session
    user_id = session["user_id"]

    # Query the database to get all the user's transactions
    transactions = db.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY transaction_datetime DESC",
        user_id
    )

    # Render the transactions in an HTML table
    return render_template("history.html", transactions=transactions)
    # return apology("TODO")

@app.route('/cart')
@login_required
def cart():
    user_id = session["user_id"]

    try:
        # Query the database to get the user's cart items along with product details
        cart = db.execute("SELECT products.id, products.name, products.price, cart.quantity FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", user_id)

        total_price = 0  # Initialize the total_price variable

        for item in cart:
            item['total'] = item['quantity'] * item['price']  # Calculate item total
            total_price += item['total']  # Add item total to total_price

            print("Cart:", cart)
            print("Total Price:", total_price)

        return render_template('cart.html', cart=cart, total_price=total_price)
    except Exception as e:
        # Handle database-related errors here
        print(f"Database error: {str(e)}")
        return apology("An error occurred while fetching cart items", 500)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    user_id = session["user_id"]

    if request.method == "POST":

        try:
            # Check if the item is already in the cart
            existing_item = db.execute("SELECT * FROM cart WHERE user_id = ? AND product_id = ?", user_id, product_id)

            if existing_item:
                # Update quantity if item is already in the cart
                db.execute("UPDATE cart SET quantity = quantity + 1 WHERE user_id = ? AND product_id = ?", user_id, product_id)
            else:
                # Insert a new item into the cart with quantity 1
                db.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)", user_id, product_id)


            print(f"Added product {product_id} to the cart for user {user_id}")

            return redirect("/")
        except Exception as e:
            # Handle database-related errors here
            print(f"Database error: {str(e)}")
            return apology("An error occurred while adding to the cart", 500)

@app.route('/update_cart/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    if request.method == 'POST':
        new_quantity = int(request.form.get('new_quantity'))

        # Update the cart in your database with the new quantity
        db.execute("UPDATE cart SET quantity = ? WHERE product_id = ?", new_quantity, item_id)

        return redirect(url_for('cart'))  # Redirect back to the cart page

@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    user_id = session["user_id"]

    if request.method == "POST":
        try:
            # Remove the item from the cart for the user
            db.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?", user_id, item_id)

            flash("Item removed from cart!", "success")
            return redirect("/cart")
        except Exception as e:
            # Handle database-related errors here
            print(f"Database error: {str(e)}")
            return apology("An error occurred while removing the item from the cart", 500)

@app.route('/checkout')
@login_required
def checkout():

    user_id = session["user_id"]

    try:
        # Query the database to get the user's cart items along with product details
        cart = db.execute("SELECT products.id, products.name, products.price, cart.quantity FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", user_id)

        total_price = 0  # Initialize the total_price variable

        for item in cart:
            item['total'] = item['quantity'] * item['price']  # Calculate item total
            total_price += item['total']  # Add item total to total_price

            print("Cart:", cart)
            print("Total Price:", total_price)

        return render_template('checkout.html', cart=cart, total_price=total_price)
    except Exception as e:
        # Handle database-related errors here
        print(f"Database error: {str(e)}")
        return apology("An error occurred while fetching cart items", 500)


@app.route('/get_cart_total', methods=['GET'])
@login_required
def get_cart_total():
    user_id = session["user_id"]

    try:
        # Query the database to calculate the total cart price
        total_price = db.execute("SELECT SUM(products.price * cart.quantity) AS total FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", user_id)[0]["total"]

        return jsonify({"total": total_price})
    except Exception as e:
        # Handle database-related errors here
        print(f"Database error: {str(e)}")
        return jsonify({"total": 0})

@app.route("/api/orders/<order_id>/capture", methods=["POST"])
def capture_paypal_payment(order_id):
    try:
        # Request access token from PayPal API
        auth_response = requests.post(
            "https://api.paypal.com/v1/oauth2/token",
            headers={"Accept": "application/json", "Accept-Language": "en_US"},
            auth=(CLIENT_ID, CLIENT_SECRET),
            data={"grant_type": "client_credentials"},
        )

        auth_data = auth_response.json()

        # Check if access token was obtained successfully
        if "access_token" not in auth_data:
            return jsonify({"error": "Failed to obtain access token from PayPal API"}), 500

        access_token = auth_data["access_token"]

        # Capture the payment
        capture_response = requests.post(
            PAYPAL_CAPTURE_URL.format(order_id=order_id),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        capture_data = capture_response.json()

        # Check if payment capture was successful
        if "status" in capture_data and capture_data["status"] == "COMPLETED":
            success = True
        else:
            success = False

        return jsonify({"success": success})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/paypal_success", methods=["GET", "POST"])
def paypal_success():
    if request.method == "POST":
        # Extract relevant details from the PayPal payment confirmation
        user_id = session["user_id"]

        # Calculate the order total dynamically based on the items in the cart
        amount = 0.0
        order_items = []
        for item in cart:
            total_price += item["price"] * item["quantity"]
            order_items.append(item["name"])  # Collect item names for the order description

        transaction_datetime = datetime.datetime.now()

        # Create a comma-separated order description
        order_name = ", ".join(order_items)

        # Insert transaction details into the database
        db.execute(
            "INSERT INTO transactions (user_id, transaction_type, order_name, price, transaction_datetime) VALUES (?, ?, ?, ?, ?)",
            (user_id, "Purchase", order_name, amount, transaction_datetime)
        )

        flash("Payment successful! Your transaction has been recorded.")
        return redirect(url_for("checkout"))
    return render_template("paypal_success.html")

if __name__ == "__main__":
    app.run()
