from extensions import db
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)

    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")  # admin, customer, guest, employee

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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


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

class AuctionItem(db.Model):
    __tablename__ = "auction_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    specs = db.Column(db.Text, nullable=True)  # store as JSON or comma-separated string
    current_bid = db.Column(db.Float, default=0.0)
    highest_bidder = db.Column(db.String(100), nullable=True)
    min_bid_increment = db.Column(db.Integer, default=10)
    auction_end_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    seller_name = db.Column(db.String(255), nullable=False)
    seller_verified = db.Column(db.Boolean, default=False)
    seller_avatar = db.Column(db.String(255), default="https://via.placeholder.com/60")