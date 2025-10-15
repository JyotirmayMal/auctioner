from datetime import datetime
import pandas as pd
import numpy as np
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import or_, func
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from models import BlogPost, Payment, User, AuctionItem, ActiveBiddingItem, Bid
from extensions import db
from collections import defaultdict

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
    # --- Auth check ---
    if "user_id" not in session or session.get("role") != "admin":
        flash("Please log in as admin.", "danger")
        return redirect(url_for("admin.login"))

    # --- Users ---
    users = User.query.filter(User.role != "admin").all()
    total_users = len(users)

    # --- Auction Items ---
    items = AuctionItem.query.all()
    total_auctions = len(items)
    active_auctions = sum(1 for item in items if item.auction_end_time > datetime.now() and not item.is_sold)
    completed_auctions = sum(1 for item in items if item.is_sold)

    # --- Payments ---
    payments = Payment.query.all()
    total_revenue = sum(p.amount for p in payments if p.status == "successful")
    pending_disputes = sum(1 for p in payments if p.status == "failed")

    # --- Active Users (Bidders) ---
    active_bidders = ActiveBiddingItem.query.filter_by(is_active=True).all()
    active_user_ids = set(ab.highest_bidder_id for ab in active_bidders if ab.highest_bidder_id)
    active_users = len(active_user_ids)

    # --- Recent Activity ---
    recent_bids = Bid.query.order_by(Bid.timestamp.desc()).limit(5).all()
    recent_payments = Payment.query.order_by(Payment.timestamp.desc()).limit(5).all()

    # --- Auction Status Chart ---
    auction_status_counts = {
        "Active": active_auctions,
        "Completed": completed_auctions
    }

    # --- Revenue by Category Chart ---
    revenue_by_category = defaultdict(float)
    for item in items:
        category = getattr(item, "category", "General")
        if item.is_sold:
            revenue_by_category[category] += item.current_bid

    # --- Top Categories by Auction Count ---
    category_counts = defaultdict(int)
    for item in items:
        category = getattr(item, "category", "General")
        category_counts[category] += 1

    # --- Prepare cards and charts ---
    cards = {
        "total_auctions": total_auctions,
        "total_revenue": "{:,.2f}".format(total_revenue),
        "active_users": active_users,
        "pending_disputes": pending_disputes,
        "total_users": total_users,
        "active_auctions": active_auctions,
        "completed_auctions": completed_auctions
    }

    charts = {
        "auction_status": auction_status_counts,
        "revenue_by_category": dict(revenue_by_category),
        "category_counts": dict(category_counts)
    }

    # --- Convert items for template ---
    items_list = [{
        "id": item.id,
        "title": item.title,
        "current_bid": item.current_bid,
        "is_sold": item.is_sold,
        "category": getattr(item, "category", "General"),
        "auction_end_time": item.auction_end_time, 
        "seller_name": item.seller_name
    } for item in items]

    # --- Convert recent activity for template ---
    recent_activity = {
        "bids": [{
            "id": bid.id,
            "item_title": bid.item.title,
            "user_name": f"{bid.user.first_name} {bid.user.last_name}",
            "bid_amount": bid.bid_amount,
            "timestamp": bid.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        } for bid in recent_bids],
        "payments": [{
            "id": payment.id,
            "user_name": f"{payment.user.first_name} {payment.user.last_name}",
            "item_title": payment.item.title,
            "amount": payment.amount,
            "status": payment.status.capitalize(),
            "timestamp": payment.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        } for payment in recent_payments]
    }

    return render_template(
        "Admin Dashboard page.html",
        admin_name=session.get("first_name"),
        items=items_list,
        users=users,
        payments=payments,
        posts=BlogPost.query.order_by(BlogPost.created_at.desc()).all(),
        now=datetime.now(),
        cards=cards,
        charts=charts,
        recent_activity=recent_activity
    )



@admin_bp.route("/add_item", methods=["POST"])
def add_item():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Please log in as admin.", "danger")
        return redirect(url_for("admin.login"))

    title = request.form.get("title")
    category = request.form.get("category")
    seller_name = request.form.get("seller_name")
    description = request.form.get("description")
    current_bid = request.form.get("current_bid", 0.0)
    min_bid_increment = request.form.get("min_bid_increment", 10)
    auction_end_time = request.form.get("auction_end_time")

    new_item = AuctionItem(
        title=title,
        description=description,
        category=category,
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


@admin_bp.route("/add_user", methods=["POST"])
def add_user():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    try:
        # Get form data
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        phone_number = request.form.get("phone_number")
        password = request.form.get("password")
        role = request.form.get("role")
        date_of_birth = request.form.get("date_of_birth")
        street_address = request.form.get("street_address")
        city = request.form.get("city")
        state_province = request.form.get("state_province")
        postal_code = request.form.get("postal_code")
        country = request.form.get("country")
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return jsonify({"success": False, "message": "Email already exists"}), 400
            
        # Check if phone number already exists
        if User.query.filter_by(phone_number=phone_number).first():
            return jsonify({"success": False, "message": "Phone number already exists"}), 400
        
        # Create new user
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            role=role,
            date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d').date(),
            street_address=street_address,
            city=city,
            state_province=state_province,
            postal_code=postal_code,
            country=country
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({"success": True, "message": "User added successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route("/get_user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    user = User.query.get_or_404(user_id)
    
    user_data = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "role": user.role,
        "date_of_birth": user.date_of_birth.strftime('%Y-%m-%d'),
        "street_address": user.street_address,
        "city": user.city,
        "state_province": user.state_province,
        "postal_code": user.postal_code,
        "country": user.country
    }
    
    return jsonify({"success": True, "user": user_data})

@admin_bp.route("/edit_user/<int:user_id>", methods=["POST"])
def edit_user(user_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Update user data
        user.first_name = request.form.get("first_name")
        user.last_name = request.form.get("last_name")
        user.email = request.form.get("email")
        user.phone_number = request.form.get("phone_number")
        user.role = request.form.get("role")
        user.date_of_birth = datetime.strptime(request.form.get("date_of_birth"), '%Y-%m-%d').date()
        user.street_address = request.form.get("street_address")
        user.city = request.form.get("city")
        user.state_province = request.form.get("state_province")
        user.postal_code = request.form.get("postal_code")
        user.country = request.form.get("country")
        
        db.session.commit()
        
        return jsonify({"success": True, "message": "User updated successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route("/toggle_user_status/<int:user_id>", methods=["POST"])
def toggle_user_status(user_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        action = data.get("action")
        
        if action == "block":
            user.role = "blocked"
        elif action == "activate":
            user.role = "customer"  # or whatever default role you want
        
        db.session.commit()
        
        return jsonify({"success": True, "message": f"User {action}ed successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route("/delete_user/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({"success": True, "message": "User deleted successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/blogs", methods=["GET"])
def blogs():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Please log in as admin.", "danger")
        return redirect(url_for("admin.login"))

    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template("Admin Dashboard page.html", posts=posts, admin_name=session.get("first_name"))

@admin_bp.route("/add_blog", methods=["POST"])
def add_blog():
    title = request.form["title"]
    category = request.form.get("category", "General")
    author = request.form.get("author", "Admin")
    content = request.form["content"]

    post = BlogPost(title=title, category=category, author=author, content=content)
    db.session.add(post)
    db.session.commit()
    flash("Blog post added successfully!", "success")
    return redirect(url_for("admin.blogs"))

@admin_bp.route("/edit_blog/<int:post_id>", methods=["POST"])
def edit_blog(post_id):
    post = BlogPost.query.get_or_404(post_id)
    post.title = request.form["title"]
    post.category = request.form.get("category")
    post.author = request.form.get("author")
    post.content = request.form.get("content")
    db.session.commit()
    flash("Blog post updated successfully!", "success")
    return redirect(url_for("admin.blogs"))

@admin_bp.route("/delete_blog/<int:post_id>", methods=["POST"])
def delete_blog(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Blog post deleted successfully!", "success")
    return redirect(url_for("admin.blogs"))

@admin_bp.route("/payments", methods=["GET"])
def payments():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Please log in as admin.", "danger")
        return redirect(url_for("admin.login"))

    payments = Payment.query.order_by(Payment.timestamp.desc()).all()
    return render_template(
        "Admin Dashboard page.html",
        payments=payments,
        admin_name=session.get("first_name")
    )