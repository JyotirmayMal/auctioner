from datetime import datetime
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from models import AuctionItem, Bid, User, ActiveBiddingItem
import json
from extensions import db

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