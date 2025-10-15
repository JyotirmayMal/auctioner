from datetime import datetime
from dateutil import parser
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
import pytz
from models import AuctionItem, Bid, User, ActiveBiddingItem
import json
from extensions import db
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

auctions_bp = Blueprint("auctions", __name__, template_folder="../../templates")

@auctions_bp.route("/")
def auctions_home():
    if "user_id" not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])

    # Fetch ActiveBiddingItem records
    active_items = (
    ActiveBiddingItem.query
    .join(AuctionItem, isouter=True)  # LEFT OUTER JOIN to include all
    .filter(ActiveBiddingItem.is_active == True)
    .order_by(ActiveBiddingItem.start_time.desc())
    .all()
)

    print("Active Items Count:", len(active_items))
    for ai in active_items:
        print("ID:", ai.id, "AuctionItem:", ai.auction_item, "Current Price:", ai.current_price)

    # Fetch latest 3 auction items
    items = AuctionItem.query.order_by(AuctionItem.id.desc()).limit(3).all()
    
    # Fetch items bought by current user
    bought_items = AuctionItem.query.filter_by(buyer_id=user.id, is_sold=True).all()
    
    # Fetch user's active bids
    user_bids = (
        Bid.query
        .filter_by(user_id=user.id)
        .join(AuctionItem)
        .filter(AuctionItem.auction_end_time > datetime.now())
        .order_by(Bid.timestamp.desc())
        .all()
    )
    print(i for i in active_items)
    return render_template(
        "Users DashBoard Page.html",
        items=items,
        user=user,
        now=datetime.now(),
        active_items=active_items,
        bought_items=bought_items,
        user_bids=user_bids
    )


@auctions_bp.route("/about")
def about_us():
    user = None
    if "user_id" in session:
        user = User.query.get(session["user_id"])
    return render_template("About Us.html", user=user)



@auctions_bp.route("/how-it-works")
def how_it_works():
    user = None
    if "user_id" in session:
        user = User.query.get(session["user_id"])
    return render_template("How It Works.html", user=user)


@auctions_bp.route("/category/<string:category_name>")
def category_page(category_name):
    user = None
    if "user_id" in session:
        user = db.session.get(User, session["user_id"])  # Updated for SQLAlchemy 2.0

    # Current time in IST
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    # Log the category name
    logger.debug(f"Fetching items for category: {category_name}")

    # Fetch items based on category
    if category_name.lower() == 'all':
        items = AuctionItem.query.filter_by(is_sold=False).order_by(AuctionItem.id.desc()).all()
    else:
        # Exact match for category
        items = AuctionItem.query.filter(AuctionItem.category == category_name, AuctionItem.is_sold == False).order_by(AuctionItem.id.desc()).all()

    logger.debug(f"Found {len(items)} items for category: {category_name}")

    if not items:
        flash(f"No items found in '{category_name}' category.", "warning")

    # Prepare items for template
    items_data = []
    for item in items:
        try:
            end_time = parser.parse(str(item.auction_end_time)).astimezone(ist)
        except ValueError as e:
            logger.error(f"Error parsing auction_end_time for item {item.id}: {e}")
            continue
        time_diff = end_time - current_time
        if time_diff.total_seconds() > 0:
            days = time_diff.days
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes = remainder // 60
            time_left = f"{days}d {hours}h {minutes}m left" if days > 0 else f"{hours}h {minutes}m left"
        else:
            time_left = "Auction ended"
        
        items_data.append({
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'current_bid': f"₹{item.current_bid:.2f}",
            'time_left': time_left,
            'image': item.image or 'https://via.placeholder.com/300',
            'category': item.category
        })

    return render_template(
        "Categories.html",
        category_name=category_name.title(),
        items=items_data,
        user=user
    )

@auctions_bp.route("/api/items", methods=["GET"])
def get_items():
    # Get categories from query parameters
    categories = request.args.get('categories', '').split(',')
    categories = [cat.strip() for cat in categories if cat.strip()]
    
    # Current time in IST
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    
    # Log the requested categories
    logger.debug(f"API request for categories: {categories}")

    # Fetch items
    query = AuctionItem.query.filter_by(is_sold=False).order_by(AuctionItem.id.desc())
    if categories:
        query = query.filter(AuctionItem.category.in_(categories))
    items = query.all()
    
    logger.debug(f"API found {len(items)} items")

    # Prepare items for JSON response
    items_data = []
    for item in items:
        try:
            end_time = parser.parse(str(item.auction_end_time)).astimezone(ist)
        except ValueError as e:
            logger.error(f"Error parsing auction_end_time for item {item.id}: {e}")
            continue
        time_diff = end_time - current_time
        if time_diff.total_seconds() > 0:
            days = time_diff.days
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes = remainder // 60
            time_left = f"{days}d {hours}h {minutes}m left" if days > 0 else f"{hours}h {minutes}m left"
        else:
            time_left = "Auction ended"
        
        items_data.append({
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'current_bid': f"₹{item.current_bid:.2f}",
            'time_left': time_left,
            'image': item.image or 'https://via.placeholder.com/300',
            'category': item.category
        })
    
    return jsonify({
        'items': items_data,
        'message': 'No items found.' if not items_data else 'Items fetched successfully.'
    })



@auctions_bp.route("/live/<int:item_id>")
def live_stream(item_id):
    if "user_id" not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for("auth.login"))
    
    user = User.query.get(session["user_id"])
    item = AuctionItem.query.get_or_404(item_id)
    estimated_min = round(item.current_bid * 1.21, 2)
    estimated_max = round(item.current_bid * 2.57, 2)
    
    return render_template(
        "Live Auction Streaming Page.html",
        item=item,
        user=user,
        est_min=estimated_min,
        est_max=estimated_max
    )


@auctions_bp.route("/bid/<int:item_id>", methods=["POST"])
def place_bid(item_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please log in to place a bid."}), 401

    item = AuctionItem.query.get_or_404(item_id)
    bid_amount = float(request.json.get("bid_amount"))
    user_id = session["user_id"]

    # Ensure auction is active
    if datetime.now() > item.auction_end_time:
        return jsonify({"success": False, "message": "Auction has ended."}), 400

    # Ensure bid is valid
    min_increment = item.min_bid_increment or 100
    min_required = item.current_bid + min_increment
    if bid_amount < min_required:
        return jsonify({"success": False, "message": f"Bid must be at least ₹{min_required}"}), 400

    # Save bid
    new_bid = Bid(item_id=item.id, user_id=user_id, bid_amount=bid_amount)
    db.session.add(new_bid)

    # Update item
    item.current_bid = bid_amount
    item.highest_bidder = user_id
    
    # Update ActiveBiddingItem if exists
    active_item = ActiveBiddingItem.query.filter_by(auction_item_id=item.id).first()
    if active_item:
        active_item.current_price = bid_amount
        active_item.highest_bidder_id = user_id
        active_item.total_bids += 1
        active_item.last_bid_time = datetime.now()
    
    db.session.commit()

    return jsonify({
        "success": True, 
        "bid_amount": bid_amount, 
        "highest_bidder": user_id,
        "message": "Bid placed successfully!"
    })