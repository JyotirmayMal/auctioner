import traceback
import razorpay
import hashlib
import hmac
from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, session, url_for, jsonify, current_app
from models import Payment, AuctionItem
from extensions import db

payments_bp = Blueprint("payments", __name__, template_folder="../../templates")

@payments_bp.route("/tracking")
def tracking():
    return render_template("Delivery Tracking Page.html")

@payments_bp.route("/checkout/<int:item_id>")
def checkout(item_id):
    if "user_id" not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for("auth.login"))

    item = AuctionItem.query.get_or_404(item_id)
    amount = float(request.args.get("amount", item.current_bid))
    
    # Calculate total amount (winning bid + premium + shipping + taxes)
    winning_bid = amount
    buyers_premium = winning_bid * 0.15
    shipping = 150.00
    taxes = winning_bid * 0.05
    total_amount = winning_bid + buyers_premium + shipping + taxes
    
    return render_template("CheckoutPayment page.html", 
                         item=item, 
                         amount=winning_bid,
                         total_amount=total_amount)

@payments_bp.route("/create-order", methods=["POST"])
def create_razorpay_order():
    if "user_id" not in session:
        return jsonify({"error": "User not logged in"}), 401
    
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Debug log
        
        if not data:
            return jsonify({"error": "No data received"}), 400
            
        item_id = data.get('item_id')
        amount = data.get('amount')
        
        if not item_id or not amount:
            return jsonify({"error": "Missing item_id or amount"}), 400
            
        item_id = int(item_id)
        amount = float(amount)
        
        print(f"Processing: item_id={item_id}, amount={amount}")  # Debug log
        
        item = AuctionItem.query.get(item_id)
        if not item:
            return jsonify({"error": "Item not found"}), 404
        
        # Check if Razorpay credentials are set
        key_id = current_app.config.get('RAZORPAY_KEY_ID')
        key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')
        
        print(f"Razorpay Key ID: {key_id[:10]}..." if key_id else "Key ID not found")  # Debug log
        
        if not key_id or not key_secret:
            return jsonify({"error": "Razorpay credentials not configured"}), 500
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(key_id, key_secret))
        
        # Create Razorpay order
        order_data = {
            'amount': int(amount * 100),  # Amount in paise
            'currency': 'INR',
            'receipt': f'order_rcptid_{item_id}_{session["user_id"]}_{int(datetime.now().timestamp())}',
            'notes': {
                'item_id': str(item_id),
                'user_id': str(session["user_id"]),
                'item_name': item.name if hasattr(item, 'name') else f'Item {item_id}'
            }
        }
        
        print(f"Creating Razorpay order with data: {order_data}")  # Debug log
        
        order = client.order.create(data=order_data)
        print(f"Razorpay order created: {order}")  # Debug log
        
        # Save payment record
        payment = Payment(
            user_id=session["user_id"],
            item_id=item_id,
            amount=amount,
            status="pending",
            razorpay_order_id=order['id']
        )
        db.session.add(payment)
        db.session.commit()
        
        print(f"Payment record saved with ID: {payment.id}")  # Debug log
        
        return jsonify({
            "order_id": order['id'],
            "amount": amount,
            "currency": "INR",
            "key": key_id
        })
        
    except Exception as e:
        print(f"Error creating Razorpay order: {str(e)}")  # Debug log
        print(f"Traceback: {traceback.format_exc()}")  # Debug log
        return jsonify({"error": f"Failed to create order: {str(e)}"}), 500

@payments_bp.route("/verify-payment", methods=["POST"])
def verify_payment():
    if "user_id" not in session:
        return jsonify({"error": "User not logged in"}), 401
    
    try:
        data = request.get_json()
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        
        # Find payment record
        payment = Payment.query.filter_by(
            razorpay_order_id=razorpay_order_id,
            user_id=session["user_id"]
        ).first()
        
        if not payment:
            return jsonify({"error": "Payment record not found"}), 404
        
        # Verify signature
        client = razorpay.Client(auth=(current_app.config['RAZORPAY_KEY_ID'], 
                                     current_app.config['RAZORPAY_KEY_SECRET']))
        
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        # Verify the signature
        try:
            client.utility.verify_payment_signature(params_dict)
            signature_valid = True
        except:
            signature_valid = False
        
        if signature_valid:
            # Update payment record
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = "successful"
            
            # Mark item as sold
            item = AuctionItem.query.get(payment.item_id)
            item.is_sold = True
            item.buyer_id = session["user_id"]
            
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "payment_id": razorpay_payment_id,
                "order_id": razorpay_order_id
            })
        else:
            payment.status = "failed"
            db.session.commit()
            return jsonify({"error": "Invalid signature"}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error verifying payment: {str(e)}")
        return jsonify({"error": "Payment verification failed"}), 500

@payments_bp.route("/payment-success")
def payment_success():
    if "user_id" not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for("auth.login"))
    
    payment_id = request.args.get('payment_id')
    order_id = request.args.get('order_id')
    
    if payment_id and order_id:
        payment = Payment.query.filter_by(
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            user_id=session["user_id"]
        ).first()
        
        if payment and payment.status == "successful":
            flash("Payment successful! Item added to your dashboard.", "success")
            return redirect(url_for("auth.dashboard"))
    
    flash("Payment verification failed.", "error")
    return redirect(url_for("auth.dashboard"))
