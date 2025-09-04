from flask import Blueprint, render_template, request

from models import BlogPost

blog_bp = Blueprint("blog", __name__, template_folder="../../templates")

@blog_bp.route("/")
def blog_home():
    query = request.args.get("q", "").strip()

    if query:
        posts = BlogPost.query.filter(
            BlogPost.title.ilike(f"%{query}%") | BlogPost.content.ilike(f"%{query}%")
        ).order_by(BlogPost.created_at.desc()).limit(5).all()
    else:
        posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(5).all()

    announcements = BlogPost.query.filter_by(category="Announcements").order_by(BlogPost.created_at.desc()).limit(2).all()
    spotlights = BlogPost.query.filter_by(category="Spotlight").order_by(BlogPost.created_at.desc()).limit(2).all()
    promotions = BlogPost.query.filter_by(category="Promotions").order_by(BlogPost.created_at.desc()).limit(2).all()
    news = BlogPost.query.filter_by(category="News").order_by(BlogPost.created_at.desc()).limit(2).all()

    return render_template(
        "Blogs and News page.html",
        posts=posts,
        announcements=announcements,
        spotlights=spotlights,
        promotions=promotions,
        news=news,
        query=query
    )

@blog_bp.route("/post/<int:post_id>")
def blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template("single_blog.html", post=post)

