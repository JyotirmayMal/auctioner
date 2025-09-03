from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import or_
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from models import User, AuctionItem
from extensions import db

admin_bp = Blueprint("admin", __name__, template_folder="../../templates")

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        admin_id = request.form.get("adminId")
        password = request.form.get("password")

        # Query admin by email or phone, with correct OR
        admin = User.query.filter(
            (User.email == admin_id) | (User.phone_number == admin_id)
        ).filter(User.role == "admin").first()

        if not admin:
            # No admin found with this ID
            print(f"❌ Login failed: Admin not found for '{admin_id}'")
            flash("Invalid Admin ID or Password", "danger")
            return render_template("Admin_Login.html")

        if admin.password_hash != password:
            print(f"❌ Login failed: Password mismatch for '{admin_id}'")
            flash("Invalid Admin ID or Password", "danger")
            return render_template("Admin_Login.html")

        # Login successful
        session["user_id"] = admin.id
        session["role"] = admin.role
        session["first_name"] = admin.first_name
        print(f"✅ Login successful for '{admin_id}'. Session: {dict(session)}")
        flash("Login successful!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("Admin_Login.html")




@admin_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Please log in as admin.", "danger")
        return redirect(url_for("admin.login"))

    users = User.query.filter(User.role != "admin").all()
    items = AuctionItem.query.all()

    return render_template(
        "Admin Dashboard page.html",
        users=users,
        items=items,
        now=datetime.now(),
        admin_name=session.get("first_name")
    )

@admin_bp.route("/add_item", methods=["POST"])
def add_item():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Please log in as admin.", "danger")
        return redirect(url_for("admin.login"))

    title = request.form.get("title")
    seller_name = request.form.get("seller_name")
    description = request.form.get("description")
    current_bid = request.form.get("current_bid", 0.0)
    min_bid_increment = request.form.get("min_bid_increment", 10)
    auction_end_time = request.form.get("auction_end_time")

    new_item = AuctionItem(
        title=title,
        description=description,
        current_bid=float(current_bid),
        min_bid_increment=int(min_bid_increment),
        auction_end_time=datetime.fromisoformat(auction_end_time),
        seller_name=seller_name,
    )
    db.session.add(new_item)
    db.session.commit()

    flash("New item created successfully!", "success")
    return redirect(url_for("admin.dashboard"))



@admin_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("admin.login"))