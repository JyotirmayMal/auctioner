from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, jsonify, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import uuid



app = Flask(__name__)
app.secret_key = 'a8f7d8c3b12e4e90af6b98d27cb3129e42dff7bd1a72c0d4974e3c60a44d7b1e'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:%40JMh05t1@localhost/shopping_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            api_key = request.headers.get('X-API-KEY')
            if not api_key:
                return jsonify({"error": "Missing API key"}), 401
            user = User.query.filter_by(api_key=api_key).first()
            if not user:
                return jsonify({"error": "Unauthorized"}), 401
            if user.role not in roles:
                return jsonify({"error": "Forbidden"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'user'

    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    street_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state_province = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Plain text password setter
    def set_password(self, password):
        self.password_hash = password

    # Plain text password checker
    def check_password(self, password):
        return self.password_hash == password


class Company(db.Model):
    __tablename__ = 'companies'
    company_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_name = db.Column(db.String(255), nullable=False)
    tax_id_number = db.Column(db.String(50), nullable=False, unique=True)
    company_address = db.Column(db.String(255), nullable=False)
    auth_contact_name = db.Column(db.String(200), nullable=False)
    auth_contact_role = db.Column(db.String(100), nullable=False)
    business_registration_proof_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def __repr__(self):
        return f'<Company {self.company_name}>'

with app.app_context():
    db.create_all()

# Define your routes
@app.route("/")
def home():
    return render_template("index.html")


@app.route('/admin-dashboard')
def admin_dashboard():
    return render_template('Admin Dashboard page.html')

@app.route('/advanced-search')
def advanced_search():
    return render_template('Advanced Search and Filter Page.html')

@app.route('/auction-home')
def auction_about():
    return render_template('About Us.html')

@app.route('/auctions')
def auctions():
    return render_template('Auctions.html')

@app.route('/blogs-news')
def blogs_news():
    return render_template('Blogs and News page.html')

@app.route('/categories')
def categories():
    return render_template('Categories.html')

@app.route('/checkout-payment')
def checkout_payment():
    return render_template('CheckoutPayment page.html')

@app.route('/delivery-tracking')
def delivery_tracking():
    return render_template('Delivery Tracking Page.html')

@app.route('/how-it-works')
def how_it_works():
    return render_template('How It Works.html')

@app.route('/live-auction-streaming')
def live_auction_streaming():
    return render_template('Live Auction Streaming Page.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Submitted username: {username}, password: {password}")
     

        user = User.query.filter_by(username=username).first()
        print(f"User found: {user}")

        if user:
            print(f"Password check result: {user.check_password(password)}")

        if user and user.check_password(password):
            session['username'] = user.username
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')
            return redirect(url_for('login'))

    return render_template('Login Page.html')




@app.route('/registration', methods=['GET'])
def registration():
    return render_template('Registration Page.html')


@app.route('/register', methods=['POST'])
def register():
    form = request.form

    username = form.get('username')
    password = form.get('password')
    role = form.get('role', 'user')

    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'error')
        return redirect(url_for('registration'))

    user = User(
        username=username,
        api_key=str(uuid.uuid4()),
        role=role,
        first_name=form.get('firstName'),
        last_name=form.get('lastName'),
        street_address=form.get('streetAddress'),
        city=form.get('city'),
        state_province=form.get('state'),
        postal_code=form.get('postalCode'),
        country=form.get('country'),
        date_of_birth=form.get('dob'),
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    flash('Registration successful. Please log in.')
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    return render_template('Users DashBoard Page.html')



if __name__ == '__main__':
    app.run(debug=True)
