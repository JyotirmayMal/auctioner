from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import AuctionItem, User
from extensions import db
import traceback
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
        try:
            # Get form data
            user_type = request.form.get("userType")
            first_name = request.form.get("firstName")
            last_name = request.form.get("lastName")
            street_address = request.form.get("streetAddress")
            city = request.form.get("city")
            state = request.form.get("state")
            postal_code = request.form.get("postalCode")
            country = request.form.get("country")
            dob = request.form.get("dob")
            email = request.form.get("email")
            phone = request.form.get("mobileNumber")
            password = request.form.get("password")
            confirm_password = request.form.get("confirmPassword")

            # Enhanced Debug: Print ALL form data
            print("=== COMPLETE FORM DATA DEBUG ===")
            print("Raw form data:", dict(request.form))
            print(f"User Type: '{user_type}' (len: {len(user_type) if user_type else 0})")
            print(f"First Name: '{first_name}' (len: {len(first_name) if first_name else 0})")
            print(f"Last Name: '{last_name}' (len: {len(last_name) if last_name else 0})")
            print(f"Street Address: '{street_address}' (len: {len(street_address) if street_address else 0})")
            print(f"City: '{city}' (len: {len(city) if city else 0})")
            print(f"State: '{state}' (len: {len(state) if state else 0})")
            print(f"Postal Code: '{postal_code}' (len: {len(postal_code) if postal_code else 0})")
            print(f"Country: '{country}' (len: {len(country) if country else 0})")
            print(f"DOB: '{dob}' (len: {len(dob) if dob else 0})")
            print(f"Email: '{email}' (len: {len(email) if email else 0})")
            print(f"Phone: '{phone}' (len: {len(phone) if phone else 0})")
            print(f"Password: {'*' * len(password) if password else 'None'} (len: {len(password) if password else 0})")
            print(f"Confirm Password: {'*' * len(confirm_password) if confirm_password else 'None'} (len: {len(confirm_password) if confirm_password else 0})")
            print("================================")

            # Server-side validation (don't trust client-side only)
            errors = []
            
            # Check required fields with detailed logging
            required_fields = {
                'userType': user_type,
                'firstName': first_name,
                'lastName': last_name,
                'streetAddress': street_address,
                'city': city,
                'state': state,
                'postalCode': postal_code,
                'country': country,
                'dob': dob,
                'email': email,
                'mobileNumber': phone,
                'password': password,
                'confirmPassword': confirm_password
            }
            
            print("=== FIELD VALIDATION ===")
            for field_name, field_value in required_fields.items():
                is_empty = not field_value or not str(field_value).strip()
                print(f"{field_name}: {'EMPTY' if is_empty else 'OK'}")
                if is_empty:
                    errors.append(f"{field_name} is required")
            print("========================")
            
            # Password validation
            if password and confirm_password:
                if password != confirm_password:
                    errors.append("Passwords do not match")
                    print("❌ Password mismatch")
                if len(password) < 8:
                    errors.append("Password must be at least 8 characters long")
                    print("❌ Password too short")
            
            # Email validation
            if email:
                import re
                email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
                if not re.match(email_pattern, email):
                    errors.append("Invalid email format")
                    print("❌ Invalid email format")
                else:
                    print("✅ Email format valid")
            
            # Check for existing users
            if email:
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    errors.append("Email already registered")
                    print("❌ Email already exists")
                else:
                    print("✅ Email available")
            
            if phone:
                existing_phone = User.query.filter_by(phone_number=phone).first()
                if existing_phone:
                    errors.append("Phone number already registered")
                    print("❌ Phone already exists")
                else:
                    print("✅ Phone available")
            
            # Date of birth validation
            dob_parsed = None
            if dob:
                try:
                    from datetime import datetime, date
                    dob_parsed = datetime.strptime(dob, "%Y-%m-%d").date()
                    
                    # Check age (must be 18+)
                    today = date.today()
                    age = today.year - dob_parsed.year - ((today.month, today.day) < (dob_parsed.month, dob_parsed.day))
                    
                    print(f"✅ DOB parsed: {dob_parsed}, Age: {age}")
                    
                    if age < 18:
                        errors.append("You must be at least 18 years old to register")
                        print("❌ Age under 18")
                        
                    if dob_parsed > today:
                        errors.append("Date of birth cannot be in the future")
                        print("❌ DOB in future")
                        
                except ValueError as e:
                    errors.append("Invalid date of birth format")
                    print(f"❌ DOB parsing error: {e}")
                    dob_parsed = None
            
            # Print all errors found
            print(f"=== VALIDATION ERRORS ({len(errors)}) ===")
            for i, error in enumerate(errors, 1):
                print(f"{i}. {error}")
            print("=====================================")
            
            # If there are validation errors, show them and return
            if errors:
                for error in errors:
                    flash(error, "error")
                print("🔄 Redirecting back to registration due to errors")
                return redirect(url_for("auth.register"))
            
            # Create new user
            print("✅ All validations passed, creating user...")
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
                role=user_type,
            )
            new_user.set_password(password)

            # Save to database
            db.session.add(new_user)
            db.session.commit()
            
            print(f"✅ User created successfully: {email}")
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("auth.login"))

        except Exception as e:
            db.session.rollback()
            print(f"❌ Registration Error: {str(e)}")
            import traceback
            traceback.print_exc()
            flash("An error occurred during registration. Please try again.", "error")
            return redirect(url_for("auth.register"))

    # GET request - show registration form
    return render_template("Registration Page.html")



@auth_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])
    print("🟢 Session in dashboard:", dict(session))

    bought_items = AuctionItem.query.filter_by(buyer_id=user.id).all()

    return render_template(
        "Users DashBoard Page.html",
        user=user,
        bought_items=bought_items
    )

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
