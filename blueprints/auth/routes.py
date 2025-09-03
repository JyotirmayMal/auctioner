from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import User
from extensions import db
import uuid

auth_bp = Blueprint("auth", __name__, template_folder="../../templates")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("username")  # could be email or username
        password = request.form.get("password")

        # Try email first, then username
        user = User.query.filter_by(email=identifier).first()
        if not user:
            user = User.query.filter_by(first_name=identifier).first()  # or username field if you have one

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["role"] = user.role
            flash("Logged in successfully", "success")
            print("✅ Login success:", session["user_id"], session["role"])
            return redirect(url_for("auth.dashboard"))

        flash("Invalid credentials", "error")
        return redirect(url_for("auth.login"))

    return render_template("Login Page.html")



@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Required fields
        first_name = request.form.get("firstName")
        last_name = request.form.get("lastName")
        street_address = request.form.get("streetAddress")
        city = request.form.get("city")
        state = request.form.get("state")
        postal_code = request.form.get("postalCode")
        country = request.form.get("country")
        dob = request.form.get("dob")  # yyyy-mm-dd
        email = request.form.get("email")
        phone = request.form.get("mobileNumber")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmPassword")

        # Validate
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered", "error")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(phone_number=phone).first():
            flash("Phone number already registered", "error")
            return redirect(url_for("auth.register"))
        
        if not dob:
            flash("Date of Birth is required", "error")
            return redirect(url_for("auth.register"))
        try:
            dob_parsed = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid Date of Birth format", "error")
            return redirect(url_for("auth.register"))

        # Create user
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            street_address=street_address,
            city=city,
            state_province=state,
            postal_code=postal_code,
            country=country,
            date_of_birth=dob_parsed,
            email=email,
            phone_number=phone,
            role="customer"  # default
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            print("❌ Registration DB Error:", e)
            flash("An error occurred while registering. Check logs.", "error")
            return redirect(url_for("auth.register"))

    return render_template("Registration Page.html")



@auth_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])
    print("🟢 Session in dashboard:", dict(session))

    return render_template(
        "Users DashBoard Page.html",
        user=user
    )

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
