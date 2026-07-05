from datetime import timedelta
from webbrowser import get

from flask import Flask, render_template, request, redirect, url_for, session, flash,jsonify
from config import Config
import sqlite3
import datetime

def convert_timestamp(val):
    val_str = val.decode('utf-8')
    try:
        return datetime.datetime.fromisoformat(val_str)
    except ValueError:
        return datetime.datetime.strptime(val_str, "%Y-%m-%d %H:%M:%S")

sqlite3.register_converter("TIMESTAMP", convert_timestamp)
from flask_mail import Mail, Message
import random
import bcrypt
import os
from werkzeug.utils import secure_filename

import razorpay

app = Flask(__name__)
app.config.from_object(Config)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=999)
mail = Mail(app)
razorpay_client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))

UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
PROFILE_IMG_FOLDER = app.config['PROFILE_IMG_FOLDER']




import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "smartcart.db")

def get_db():
    connection = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    connection.row_factory = sqlite3.Row
    return connection

@app.route('/')
def index():

    return render_template('admin/index.html')


@app.route('/admin-signup', methods=['GET', 'POST'])
def admin_signup():

    if request.method == "GET":
        return render_template("admin/signup.html")

    name = request.form['name']
    email = request.form['email']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT admin_id FROM admin WHERE email=?", (email,))
    existing_admin = cursor.fetchone()
    cursor.close()
    conn.close()

    if existing_admin:
        flash("This email is already registered. Please login instead.", "danger")
        return redirect('/admin-signup')

    session['signup_name'] = name
    session['signup_email'] = email

    otp = random.randint(100000, 999999)
    session['otp'] = otp

    message = Message(
        subject="SmartCart Admin OTP",
        sender=app.config['MAIL_USER'],
        recipients=[email]
    )
    message.body = f"Your OTP for SmartCart Admin Registration is: {otp}"
    mail.send(message)

    flash("OTP sent to your email!", "success")
    return redirect('/verify-otp')



@app.route('/verify-otp', methods=['POST','GET'])
def verify_otp():
    if request.method == "GET":
        return render_template("admin/verify_otp.html")

    user_otp = request.form['otp']

    if str(session.get('otp')) != str(user_otp):

        return jsonify({
            "success": False
        })

    session["otp_verified"] = True
    session.pop("otp", None)
    

    return jsonify({
        "success": True
    })
    

@app.route('/complete-signup', methods=['POST'])
def complete_signup():

    if not session.get("otp_verified"):

        flash("Verify OTP first.")
        return redirect("/verify-otp")

    password = request.form["password"]

    hashed_password = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    )

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO admin(name,email,password)
        VALUES(?,?,?)
        """,
        (
            session['signup_name'],
            session['signup_email'],
            hashed_password
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    session.pop("otp_verified", None)
    session.pop("signup_name", None)
    session.pop("signup_email", None)

    flash("Registration Successful! Please Sign In.", "success")

    return redirect("/admin-signin")

@app.route('/admin-signin', methods=['GET', 'POST'])
def admin_signin():

    if request.method == "GET":
        return render_template("admin/signin.html")

    email = request.form['email']
    password = request.form['password']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin WHERE email=?", (email,))
    admin = cursor.fetchone()
    cursor.close()
    conn.close()

    stored_password = admin['password']
    if isinstance(stored_password, str):
        stored_password = stored_password.encode('utf-8')

    if not admin or not bcrypt.checkpw(password.encode('utf-8'), stored_password):
        flash("Invalid email or password.", "danger")
        return redirect('/admin-signin')

    session['admin_id'] = admin['admin_id']
    session['admin_name'] = admin['name']

    flash("Login Successful!", "success")
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if not session.get('admin_id'):
        flash("Please login first.", "danger")
        return redirect('/admin-signin')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin/dashboard.html', name=session.get('admin_name'), products=products)

@app.route('/admin/profile', methods=['GET', 'POST'])
def admin_profile():

    if 'admin_id' not in session:
        flash("Please login!", "danger")
        return redirect('/admin-signin')

    admin_id = session['admin_id']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM admin WHERE admin_id = ?", (admin_id,))
    admin = cursor.fetchone()

    cursor.close()
    conn.close()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        profile_image = request.files['profile_image']

        conn = get_db()

        cursor = conn.cursor()
        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("UPDATE admin SET name=?, email=?, password=? WHERE admin_id=?", (name, email, hashed_password, admin_id))
        else:
            cursor.execute("UPDATE admin SET name=?, email=? WHERE admin_id=?", (name, email, admin_id))

        if profile_image:
            filename = secure_filename(profile_image.filename)
            profile_image_path = os.path.join(PROFILE_IMG_FOLDER, filename)
            profile_image.save(profile_image_path)
            cursor.execute("UPDATE admin SET profile_image=? WHERE admin_id=?", (filename, admin_id))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Profile updated successfully!", "success")
        return redirect('/admin/profile')

    return render_template("admin/admin_profile.html", admin=admin)


@app.route('/admin/add-product',methods=['GET','POST'])
def add_product():
    if not session.get('admin_id'):
        flash("Please login first.", "danger")
        return redirect('/admin-signin')

    if request.method == "GET":
        return render_template("admin/add_product.html")

    name = request.form['name']
    description = request.form['description']
    category = request.form['category']
    price = request.form['price']
    image = request.files['image']

    if image:
        filename = secure_filename(image.filename)
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        image.save(image_path)
    else:
        image_path = None

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO products(name,description,category,price,image_name)
        VALUES(?,?,?,?,?)
        """,
        (
            name,
            description,
            category,
            price,
            filename
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    flash("Product added successfully!", "success")
    return redirect('/dashboard')

@app.route('/admin/product-list')
def product_list():

    if 'admin_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/admin-login')

    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    


    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT category FROM products")
    categories = cursor.fetchall()

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search:
        query += " AND name LIKE ?"
        params.append("%" + search + "%")

    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    cursor.execute(query, params)
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin/product_list.html",
        products=products,
        categories=categories
    )



@app.route('/admin/update-product/<int:product_id>', methods=['GET', 'POST'])
def update_product(product_id):

    if 'admin_id' not in session:
        flash("Please login!", "danger")
        return redirect('/admin-login')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()

    if not product:
        cursor.close()
        conn.close()
        flash("Product not found!", "danger")
        return redirect('/admin/product-list')

    if request.method == "GET":
        cursor.close()
        conn.close()
        return render_template("admin/update_product.html", product=product)

    if request.method == "POST":

        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        price = request.form['price']

        new_image = request.files['image']

        old_image_name = product['image_name']

        if new_image and new_image.filename != "":

            from werkzeug.utils import secure_filename

            new_filename = secure_filename(new_image.filename)

            new_image_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            new_image.save(new_image_path)

            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image_name)

            if os.path.exists(old_image_path):
                os.remove(old_image_path)

            final_image_name = new_filename

        else:
            final_image_name = old_image_name

        cursor.execute("""
            UPDATE products
            SET name=?,
                description=?,
                category=?,
                price=?,
                image_name=?
            WHERE product_id=?
        """, (
            name,
            description,
            category,
            price,
            final_image_name,
            product_id
        ))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Product updated successfully!", "success")
        return redirect('/admin/product-list')

@app.route('/admin/view-product/<int:product_id>')
def view_product(product_id):

    if 'admin_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/admin-login')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()

    cursor.close()
    conn.close()

    if not product:
        flash("Product not found!", "danger")
        return redirect('/admin/product-list')

    return render_template("admin/view_product.html", product=product)

@app.route('/admin/delete-product/<int:product_id>', methods=['GET'])
def delete_product(product_id):

    if 'admin_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/admin-login')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()

    if not product:
        cursor.close()
        conn.close()
        flash("Product not found!", "danger")
        return redirect('/admin/product-list')

    cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
    conn.commit()

    image_name = product['image_name']
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)

    if os.path.exists(image_path):
        os.remove(image_path)

    cursor.close()
    conn.close()

    flash("Product deleted successfully!", "success")
    return redirect('/admin/product-list')



@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

# user routes

@app.route('/user')
def user_index():
    return render_template('user/index.html')

@app.route('/user-signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == "GET":
        return render_template("user/signup.html")

    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE email=?", (email,))
    existing_user = cursor.fetchone()
    cursor.close()
    conn.close()

    if existing_user:
        flash("This email is already registered. Please login instead.", "danger")
        return redirect('/user-signup')

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users(name,email,password)
        VALUES(?,?,?)
        """,
        (
            name,
            email,
            hashed_password
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    flash("Registration Successful! Please Sign In.", "success")
    return redirect("/user-signin")


@app.route('/user-signin', methods=['GET', 'POST'])
def user_signin():

    if request.method == "GET":
        return render_template("user/signin.html")
    email = request.form['email']
    password = request.form['password']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if not user:
        flash("Invalid email or password.", "danger")
        return redirect('/user-signin')
    stored_password = user['password']
    if isinstance(stored_password, str):
        stored_password = stored_password.encode('utf-8')

    if not bcrypt.checkpw(password.encode('utf-8'), stored_password):
        flash("Invalid email or password.", "danger")
        return redirect('/user-signin')
    
    session['user_id'] = user['user_id']
    session['user_name'] = user['name']
    session['user_email'] = user['email']

    flash("Login Successful!", "success")
    return redirect('/user-dashboard')

@app.route('/user-dashboard')
def user_dashboard():
    if not session.get('user_id'):
        flash("Please login first.", "danger")
        return redirect('/user-signin')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('user/home.html', user_name=session.get('user_name'), products=products)

@app.route('/user/products')
def user_products_list():

    if 'user_id' not in session:
        flash("Please login to view products!", "danger")
        return redirect('/user-signin')

    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT category FROM products")
    categories = cursor.fetchall()

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search:
        query += " AND name LIKE ?"
        params.append("%" + search + "%")

    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    cursor.execute(query, params)
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "user/products_list.html",
        products=products,
        categories=categories
    )


@app.route('/user/product/<int:product_id>')
def user_product_details(product_id):
    if not session['user_id'] :
        flash("Please login first!", "danger")
        return redirect('/user-signin')
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE product_id=?",(product_id,))
    product = cursor.fetchone()

    cursor.close()
    conn.close()

    if not product :
        flash('Product not found','danger')
        return redirect('/user/products')
    return render_template('user/product_details.html', product=product)


def _cart_key():
    """Return a user-specific session key for the cart, e.g. 'cart_5'."""
    return f"cart_{session['user_id']}"

@app.route('/user/add-to-cart/<int:product_id>')
def add_to_cart(product_id):

    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/user-signin')

    key = _cart_key()
    if key not in session:
        session[key] = {}

    cart = session[key]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE product_id=?", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    if not product:
        flash("Product not found.", "danger")
        return redirect(request.referrer)

    pid = str(product_id)

    if pid in cart:
        cart[pid]['quantity'] += 1
    else:
        cart[pid] = {
            'name': product['name'],
            'price': float(product['price']),
            'image': product['image_name'],
            'quantity': 1
        }

    session[key] = cart

    flash("Item added to cart!", "success")
    # return redirect('/user/cart')    
    return redirect(request.referrer) 


@app.route('/user/cart')
def view_cart():

    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/user-login')

    cart_items = session.get(_cart_key(), {})

    grand_total = sum(item['price'] * item['quantity'] for item in cart_items.values())

    return render_template("user/cart.html", cart_items=cart_items, grand_total=grand_total)

@app.route('/user/cart/increment/<pid>', methods=['POST'])
def increase_quantity(pid):
    key = _cart_key()
    cart = session.get(key, {})
    
    if pid in cart:
        cart[pid]['quantity'] += 1
        
    session[key] = cart
    grand_total = sum(item['price'] * item['quantity'] for item in cart.values())
    
    if pid in cart:
        return jsonify({
            'success': True,
            'quantity': cart[pid]['quantity'],
            'item_total': cart[pid]['price'] * cart[pid]['quantity'],
            'grand_total': grand_total
        })
    return jsonify({'success': False})

@app.route('/user/cart/decrement/<pid>', methods=['POST'])
def decrease_quantity(pid):
    key = _cart_key()
    cart = session.get(key, {})
    
    removed = False
    if pid in cart:
        cart[pid]['quantity'] -= 1
        
        if cart[pid]['quantity'] <= 0:
            cart.pop(pid)
            removed = True
            
    session[key] = cart
    grand_total = sum(item['price'] * item['quantity'] for item in cart.values())
    cart_empty = len(cart) == 0
    
    if removed:
        return jsonify({
            'success': True,
            'removed': True,
            'grand_total': grand_total,
            'cart_empty': cart_empty
        })
    elif pid in cart:
        return jsonify({
            'success': True,
            'removed': False,
            'quantity': cart[pid]['quantity'],
            'item_total': cart[pid]['price'] * cart[pid]['quantity'],
            'grand_total': grand_total
        })
    return jsonify({'success': False})

@app.route('/user/cart/remove/<pid>', methods=['POST'])
def remove_from_cart(pid):
    key = _cart_key()
    cart = session.get(key, {})
    
    if pid in cart:
        cart.pop(pid)
        
    session[key] = cart
    grand_total = sum(item['price'] * item['quantity'] for item in cart.values())
    cart_empty = len(cart) == 0
    
    return jsonify({
        'success': True,
        'removed': True,
        'grand_total': grand_total,
        'cart_empty': cart_empty
    })


@app.route('/user/profile', methods=['GET', 'POST'])
def user_profile():

    if 'user_id' not in session:
        flash("Please login!", "danger")
        return redirect('/user-signin')

    user_id = session['user_id']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        profile_image = request.files['profile_image']

        conn = get_db()

        cursor = conn.cursor()
        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("UPDATE users SET name=?, email=?, password=? WHERE user_id=?", (name, email, hashed_password, user_id))
        else:
            cursor.execute("UPDATE users SET name=?, email=? WHERE user_id=?", (name, email, user_id))

        if profile_image:
            filename = secure_filename(profile_image.filename)
            profile_image_path = os.path.join(PROFILE_IMG_FOLDER, filename)
            profile_image.save(profile_image_path)
            cursor.execute("UPDATE users SET profile_image=? WHERE user_id=?", (filename, user_id))

        conn.commit()
        cursor.close()
        conn.close()

        session['user_name'] = name
        session['user_email'] = email

        flash("Profile updated successfully!", "success")
        return redirect('/user/profile')

    return render_template("user/user_profile.html", user=user)


@app.route('/user-logout')
def user_logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('user_signin'))

import re

@app.route('/user/cart/checkout_selection', methods=['POST'])
def checkout_selection():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Please login first!"})
    
    data = request.json
    if not data or not data.get('items'):
        return jsonify({"success": False, "message": "No items selected."})
    
    session['checkout_items'] = data['items']
    return jsonify({"success": True})

@app.route('/user/checkout', methods=['GET'])
def checkout():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/user-signin')

    checkout_items = session.get('checkout_items', [])
    if not checkout_items:
        flash("Please select items to checkout.", "warning")
        return redirect('/user/cart')
    
    conn = get_db()
    cursor = conn.cursor()

    
    cursor.execute("SELECT address FROM users WHERE user_id = ?", (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    raw_address = user['address'] if user else None
    parsed_address = {}
    display_address = ""

    if raw_address:
        fields = raw_address.split('#$#$')
        if len(fields) == 9:
            parsed_address = {
                'full_name': fields[0],
                'phone': fields[1],
                'address': fields[2],
                'landmark': fields[3],
                'city': fields[4],
                'district': fields[5],
                'state': fields[6],
                'country': fields[7],
                'pincode': fields[8]
            }
            display_address = ", ".join(filter(None, fields))

    grand_total = sum(float(item['price']) * int(item['quantity']) for item in checkout_items)

    return render_template('user/checkout.html', 
                           checkout_items=checkout_items, 
                           grand_total=grand_total,
                           parsed_address=parsed_address,
                           display_address=display_address)

@app.route('/user/add-address', methods=['POST'])
def add_address():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/user-signin')

    fields = [
        request.form.get('full_name', '').strip(),
        request.form.get('phone', '').strip(),
        request.form.get('address', '').strip(),
        request.form.get('landmark', '').strip(),
        request.form.get('city', '').strip(),
        request.form.get('district', '').strip(),
        request.form.get('state', '').strip(),
        request.form.get('country', '').strip(),
        request.form.get('pincode', '').strip()
    ]
    
    address_str = '#$#$'.join(fields)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET address = ? WHERE user_id = ?", (address_str, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Address updated successfully!", "success")
    return redirect('/user/checkout')

import traceback

@app.route('/user/pay', methods=['GET'])
def user_pay():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/user-signin')

    checkout_items = session.get('checkout_items', [])
    if not checkout_items:
        flash("Cart is empty.", "warning")
        return redirect('/user/cart')

    grand_total = sum(float(item['price']) * int(item['quantity']) for item in checkout_items)
    order_amount = int(grand_total * 100) # paise
    
    try:
        razorpay_order = razorpay_client.order.create({
            'amount': order_amount,
            'currency': 'INR',
            'receipt': f'order_rcptid_{random.randint(1000, 9999)}',
            'payment_capture': '1'
        })
        
        session['razorpay_order_id'] = razorpay_order['id']
        
        return render_template('user/payment.html', 
                               key_id=app.config['RAZORPAY_KEY_ID'], 
                               amount=grand_total, 
                               order_id=razorpay_order['id'])
    except Exception as e:
        app.logger.error("Error creating Razorpay order: %s", str(e))
        flash("Error creating payment order.", "danger")
        return redirect('/user/checkout')


@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    if 'user_id' not in session:
        flash("Please login to complete the payment.", "danger")
        return redirect('/user-signin')

    razorpay_payment_id = request.form.get('razorpay_payment_id')
    razorpay_order_id = request.form.get('razorpay_order_id')
    razorpay_signature = request.form.get('razorpay_signature')

    if not (razorpay_payment_id and razorpay_order_id and razorpay_signature):
        flash("Payment verification failed (missing data).", "danger")
        return redirect('/user/cart')

    payload = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }

    try:
        razorpay_client.utility.verify_payment_signature(payload)
    except Exception as e:
        app.logger.error("Razorpay signature verification failed: %s", str(e))
        flash("Payment verification failed. Please contact support.", "danger")
        return redirect('/user/cart')

    user_id = session['user_id']
    checkout_items = session.get('checkout_items', [])

    if not checkout_items:
        flash("Cart is empty. Cannot create order.", "danger")
        return redirect('/user/products')

    total_amount = sum(float(item['price']) * int(item['quantity']) for item in checkout_items)

    conn = get_db()
    cursor = conn.cursor()

    try:



        cursor.execute("""
            INSERT INTO orders (user_id, razorpay_order_id, razorpay_payment_id, amount, payment_status)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, razorpay_order_id, razorpay_payment_id, total_amount, 'paid'))

        order_db_id = cursor.lastrowid 

        for item in checkout_items:
            product_id = int(item['pid'])
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
                VALUES (?, ?, ?, ?, ?)
            """, (order_db_id, product_id, item['name'], item['quantity'], item['price']))

        conn.commit()

        cart_key = f"cart_{user_id}"
        user_cart = session.get(cart_key, {})
        for item in checkout_items:
            pid = str(item['pid'])
            if pid in user_cart:
                user_cart.pop(pid)
        session[cart_key] = user_cart

        session.pop('checkout_items', None)
        session.pop('razorpay_order_id', None)

        flash("Payment successful and order placed!", "success")
        return redirect(f"/user/order-success/{order_db_id}")

    except Exception as e:
        conn.rollback()
        app.logger.error("Order storage failed: %s\n%s", str(e), traceback.format_exc())
        flash("There was an error saving your order. Contact support.", "danger")
        return redirect('/user/cart')
    finally:
        cursor.close()
        conn.close()

@app.route('/user/order-success/<int:order_db_id>')
def order_success(order_db_id):
    if 'user_id' not in session:
        flash("Please login!", "danger")
        return redirect('/user-signin')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE order_id=? AND user_id=?", (order_db_id, session['user_id']))
    order = cursor.fetchone()

    cursor.execute("SELECT * FROM order_items WHERE order_id=?", (order_db_id,))
    items = cursor.fetchall()

    cursor.close()
    conn.close()

    if not order:
        flash("Order not found.", "danger")
        return redirect('/user/products')

    return render_template("user/order_success.html", order=order, items=items)

@app.route('/user/my-orders')
def my_orders():
    if 'user_id' not in session:
        flash("Please login!", "danger")
        return redirect('/user-signin')

    conn = get_db()
    cursor = conn.cursor()

    # Check if orders table exists first, if not just return empty
    try:
        cursor.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (session['user_id'],))
        orders = cursor.fetchall()
    except:
        orders = []

    cursor.close()
    conn.close()

    return render_template("user/my_orders.html", orders=orders)


from flask import make_response
from utils.pdf_generator import generate_pdf

@app.route("/user/download-invoice/<int:order_id>")
def download_invoice(order_id):
    if 'user_id' not in session:
        flash("Please login!", "danger")
        return redirect('/user-signin')
 
    conn = get_db()
    cursor = conn.cursor()
 
    cursor.execute("SELECT * FROM orders WHERE order_id=? AND user_id=?",
                   (order_id, session['user_id']))
    order = cursor.fetchone()
 
    cursor.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,))
    items = cursor.fetchall()
 
    cursor.close()
    conn.close()
 
    if not order:
        flash("Order not found.", "danger")
        return redirect('/user/my-orders')
 
    html = render_template("user/invoice.html", order=order, items=items)
 
    pdf = generate_pdf(html)
    if not pdf:
        flash("Error generating PDF", "danger")
        return redirect('/user/my-orders')
 
    response = make_response(pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f"attachment; filename=invoice_{order_id}.pdf"
 
    return response

if __name__ == '__main__':
    app.run(debug=True)