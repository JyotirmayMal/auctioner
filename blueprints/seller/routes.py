from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models import AuctionItem, User, ActiveBiddingItem
from datetime import datetime

seller_bp = Blueprint('seller', __name__, template_folder='templates')


@seller_bp.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in first", "error")
        return redirect(url_for("auth.login"))

    user = User.query.get(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("auth.login"))

    # Fetch items listed by this seller
    seller_items = AuctionItem.query.filter_by(seller_name=f"{user.first_name} {user.last_name}").all()

    return render_template("seller_dashboard.html", user=user, items=seller_items, now=datetime.now())


@seller_bp.route("/publish_item", methods=["POST"])
def publish_item():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in first", "error")
        return redirect(url_for("auth.login"))

    user = User.query.get(user_id)

    is_active = 'is_active' in request.form  # ✅ safe checkbox handling

    new_item = AuctionItem(
    title=request.form["title"],
    description=request.form["description"],
    image=request.form["image_url"],
    category=request.form["category"],  # ✅ Add this line
    current_bid=request.form["reserve_price"],
    seller_name=f"{user.first_name} {user.last_name}",
    auction_end_time=datetime.strptime(request.form["auction_end_time"], "%Y-%m-%dT%H:%M"),
    is_sold=False,
    )
    db.session.add(new_item)
    db.session.commit()

    # ✅ Only create ActiveBiddingItem if Active checkbox was checked
    if is_active:
        active_bid = ActiveBiddingItem(
            auction_item_id=new_item.id,  # or auction_item_id=new_item.id — check your model name
            current_price=float(request.form.get("reserve_price", 0)),
            highest_bidder_id=None,
            start_time=datetime.now(),
            end_time=new_item.auction_end_time,
            is_active=True
        )
        db.session.add(active_bid)
        db.session.commit()

    flash("Item published successfully!", "success")
    return redirect(url_for("seller.dashboard"))

