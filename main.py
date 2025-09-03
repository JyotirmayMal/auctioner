from flask import Flask, render_template
from extensions import db
from config import Config

# Import blueprints
from blueprints.auth.routes import auth_bp
from blueprints.admin.routes import admin_bp
from blueprints.auctions.routes import auctions_bp
from blueprints.payments.routes import payments_bp
from blueprints.blog.routes import blog_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(auctions_bp, url_prefix="/auctions")
    app.register_blueprint(payments_bp, url_prefix="/payments")
    app.register_blueprint(blog_bp, url_prefix="/blog")

    @app.route("/")
    def home():
        return render_template("index.html")

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
