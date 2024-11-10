import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt
from flaskblog.forms import (
    RegistrationForm,
    LoginForm,
    UpdateAccountForm,
    PostForm,
    SearchForm,
)
from flaskblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
import requests
import json
from flask import jsonify
from dotenv import load_dotenv
load_dotenv()

@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.all()
    posts = posts[::-1]
    return render_template("home.html", posts=posts)


@app.route("/about")
def about():
    return render_template("about.html", title="About")


@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)


# creating a search function
@app.route("/search")
def search():
    # Get the search query from URL parameters (GET request)
    search_query = request.args.get("searched", "")
    print(search_query)
    # Use SQLAlchemy to filter posts by company name using case-insensitive matching
    results = Post.query.filter(Post.title.ilike(f"%{search_query}%")).all()

    # Render the search results page with matched posts
    return render_template("search.html", results=results, query=search_query)


@app.route("/summarise", methods=["POST"])
def summarise():
    # Create the document to summarize.
    data=request.get_json()
    results=data.get("results", [])

    doc = "Generate the summary for the following experiences:"
    for i, res in enumerate(results):
        if i >= 5:
            break
        doc += " " + res

    # Send request to Hugging Face API
    response = requests.post(
        url=os.getenv("url"),
        headers={"Authorization": os.getenv("token")},
        json={"inputs": doc},
    )

    # Check for errors and extract summary
    if response.status_code == 200:
        summary = response.json()
        return jsonify(summary)
    else:
        return jsonify({"error": response.text}), response.status_code


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hased_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data,
            name=form.name.data,
            email=form.email.data,
            password=hased_password,
        )
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created! You are now able to login ", "success")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash("Login Unsuccessful. Please check email  and password", "danger")
    return render_template("login.html", title="Login", form=form)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    return render_template("admin.html", title="Admin")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, "static/profile_pics", picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated!", "success")
        return redirect(url_for("account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for("static", filename="profile_pics/" + current_user.image_file)
    return render_template(
        "account.html", title="Account", image_file=image_file, form=form
    )


@app.route("/post/new", methods=["GET", "POST"])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            type=form.type.data,
            branch=form.branch.data,
            role=form.role.data,
            round=form.round.data,
            interview_date=form.interview_date.data,
            content=form.content.data,
            verdict=form.verdict.data,
            author=current_user,
        )
        db.session.add(post)
        db.session.commit()
        flash("Your post has been created!", "success")
        return redirect(url_for("home"))
    return render_template(
        "create_post.html", title="New Post", form=form, legend="New Post"
    )


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post.html", title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=["GET", "POST"])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.content = form.content.data
        db.session.commit()
        flash("Your post has been updated", "success")
        return redirect(url_for("post", post_id=post.id))
    elif request.method == "GET":
        form.content.data = post.content
        form.role.data = post.role
        form.title.data = post.title
    return render_template(
        "create_post.html", title="Update Post", form=form, legend="Update Post"
    )


@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("your post has been deleted!", "success")
    return redirect(url_for("home"))
