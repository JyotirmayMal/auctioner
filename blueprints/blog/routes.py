from flask import Blueprint, render_template

blog_bp = Blueprint("blog", __name__, template_folder="../../templates")

@blog_bp.route("/")
def blog_home():
    return render_template("Blogs and News page.html")
