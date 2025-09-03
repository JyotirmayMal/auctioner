from flask import Blueprint, render_template
from models import AuctionItem
import json

auctions_bp = Blueprint("auctions", __name__, template_folder="../../templates")

@auctions_bp.route("/")
def auctions_home():
    items = AuctionItem.query.all()

    # Convert specs from JSON/text to Python list
    auction_items = []
    for item in items:
        auction_items.append({
            "id": item.id,
            "title": item.title,
            "image": item.image,
            "description": item.description,
            "specs": json.loads(item.specs) if item.specs else [],
            "currentBid": item.current_bid,
            "highestBidder": item.highest_bidder,
            "minBidIncrement": item.min_bid_increment,
            "auctionEndTime": item.auction_end_time.isoformat(),
            "seller": {
                "name": item.seller_name,
                "verified": item.seller_verified,
                "avatar": item.seller_avatar
            }
        })

    return render_template("Auctions.html", auction_items=auction_items)


@auctions_bp.route("/live")
def live_stream():
    return render_template("Live Auction Streaming Page.html")
