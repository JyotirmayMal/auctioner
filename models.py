from extensions import db
from datetime import datetime
from enum import Enum

from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)

    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, customer, guest, employee

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

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class AuctionItem(db.Model):
    __tablename__ = "auction_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    image = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    specs = db.Column(db.Text, nullable=True)  # store as JSON or comma-separated string
    category = db.Column(db.String(100), nullable=False)
    current_bid = db.Column(db.Float, default=0.0)
    highest_bidder = db.Column(db.String(100), nullable=True)
    min_bid_increment = db.Column(db.Integer, default=10)
    auction_end_time = db.Column(db.DateTime, nullable=False, default=datetime.now)
    seller_name = db.Column(db.String(255), nullable=False)
    seller_verified = db.Column(db.Boolean, default=False)
    seller_avatar = db.Column(db.String(255), default="https://via.placeholder.com/60")
    # Track highest bidder
    highest_bidder = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    is_sold = db.Column(db.Boolean, default=False)

    # Relationships
    highest_bidder_user = db.relationship("User", foreign_keys=[highest_bidder], backref="winning_items", lazy=True)
    buyer = db.relationship("User", foreign_keys=[buyer_id], backref="purchased_items", lazy=True)

class ActiveBiddingItem(db.Model):
    __tablename__ = "active_bidding_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    auction_item_id = db.Column(db.Integer, db.ForeignKey("auction_items.id"), nullable=False)
    current_price = db.Column(db.Float, nullable=False, default=0.0)
    highest_bidder_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    total_bids = db.Column(db.Integer, default=0)
    start_time = db.Column(db.DateTime, default=datetime.now)
    end_time = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_bid_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    auction_item = db.relationship("AuctionItem", backref=db.backref("active_bidding", uselist=False))
    highest_bidder = db.relationship("User", backref="active_bids")

    def __repr__(self):
        return f"<ActiveBiddingItem {self.auction_item.title} - Current: {self.current_price}>"


class BlogPost(db.Model):
    __tablename__ = "blog_posts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), default="Admin")
    category = db.Column(db.String(100), default="General")  # e.g., Announcement, Update, FAQ
    image = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Bid(db.Model):
    __tablename__ = "bids"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("auction_items.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    bid_amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship("User", backref="bids")
    item = db.relationship("AuctionItem", backref="bids")


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("auction_items.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending / successful / failed
    razorpay_order_id = db.Column(db.String(100), nullable=True)
    razorpay_payment_id = db.Column(db.String(100), nullable=True)
    razorpay_signature = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    user = db.relationship("User", backref="payments")
    item = db.relationship("AuctionItem", backref="payments")