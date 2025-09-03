from flask import Blueprint, render_template

payments_bp = Blueprint("payments", __name__, template_folder="../../templates")

@payments_bp.route("/checkout")
def checkout():
    return render_template("CheckoutPayment page.html")

@payments_bp.route("/tracking")
def tracking():
    return render_template("Delivery Tracking Page.html")
