from datetime import datetime
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from models import AuctionItem, Bid, User
import json
from extensions import db

auctions_bp = Blueprint("auctions", __name__, template_folder="../../templates")

@auctions_bp.route("/")
def auctions_home():
    if "user_id" not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])
    items = AuctionItem.query.order_by(AuctionItem.id.desc()).limit(3).all()

    # Convert specs from JSON/text to Python list
    # auction_items = []
    # for item in items:
    #     auction_items.append({
    #         "id": item.id,
    #         "title": item.title,
    #         "image": item.image,
    #         "description": item.description,
    #         "specs": json.loads(item.specs) if item.specs else [],
    #         "currentBid": item.current_bid,
    #         "highestBidder": item.highest_bidder,
    #         "minBidIncrement": item.min_bid_increment,
    #         "auctionEndTime": item.auction_end_time.isoformat(),
    #         "seller": {
    #             "name": item.seller_name,
    #             "verified": item.seller_verified,
    #             "avatar": item.seller_avatar
    #         }
    #     })

    return render_template("Users DashBoard Page.html", items=items, user=user, now=datetime.now())


@auctions_bp.route("/live/<int:item_id>")
def live_stream(item_id):
    item = AuctionItem.query.get_or_404(item_id)
    estimated_min = round(item.current_bid * 1.21, 2)
    estimated_max = round(item.current_bid * 2.57, 2)
    return render_template(
        "Live Auction Streaming Page.html",
        item=item,
        est_min=estimated_min,
        est_max=estimated_max
    )



# @auctions_bp.route("/bid/<int:item_id>", methods=["POST"])
# def place_bid(item_id):
#     if "user_id" not in session:
#         return jsonify({"success": False, "message": "Please log in first."}), 403

#     bid_amount = request.json.get("amount")
#     item = AuctionItem.query.get_or_404(item_id)

#     if bid_amount < item.current_bid + item.min_bid_increment:
#         return jsonify({"success": False, "message": "Bid too low."}), 400

#     # Update auction item
#     item.current_bid = bid_amount
#     item.highest_bidder = session["user_id"]

#     # Save bid record
#     new_bid = Bid(
#         item_id=item.id,
#         user_id=session["user_id"],
#         bid_amount=bid_amount,
#         timestamp=datetime.now()
#     )
#     db.session.add(new_bid)
#     db.session.commit()

#     return jsonify({"success": True, "newBid": bid_amount, "highestBidder": session["first_name"]})

@auctions_bp.route("/bid/<int:item_id>", methods=["POST"])
def place_bid(item_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please log in to place a bid."}), 401

    item = AuctionItem.query.get_or_404(item_id)
    bid_amount = float(request.json.get("bid_amount"))
    user_id = session["user_id"]

    # Ensure auction is active
    if datetime.now() > item.auction_end_time:
        print("check 1")
        return jsonify({"success": False, "message": "Auction has ended."}), 400

    # Ensure bid is valid
    min_increment = item.min_bid_increment or 100
    min_required = item.current_bid + min_increment
    if bid_amount < min_required:
        print("check 2")
        return jsonify({"success": False, "message": f"Bid must be at least {min_required}"}), 400

    # Save bid
    new_bid = Bid(item_id=item.id, user_id=user_id, bid_amount=bid_amount)
    db.session.add(new_bid)

    # Update item
    item.current_bid = bid_amount
    item.highest_bidder = user_id
    db.session.commit()

    return jsonify({"success": True, "bid_amount": bid_amount, "highest_bidder": user_id})
