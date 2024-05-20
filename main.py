import os
from datetime import date
from functools import wraps
from os import abort

from flask import Flask, render_template, flash, redirect, url_for, request, session, jsonify
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import LoginManager, login_user, current_user, UserMixin, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.testing import db
from sqlalchemy.testing.pickleable import User
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from forms import RegisterForm, LoginForm, ProductForm, CreatePostForm, CommentForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# For adding profile images to the comment section
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy()
db.init_app(app)


# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")


# Create a User table for all your registered users
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")
    orders = relationship("Order", back_populates="user")


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    date = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=False)
    user = relationship("User", back_populates="orders")


# Create a table for the comments on the blog posts
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image = db.Column(db.String(100), nullable=False)


with app.app_context():
    db.create_all()



@app.route("/")
def home():
    return render_template("home.html")


@app.route("/sklep")
def sklep():
    return render_template("sklep.html")


@app.route('/aukcja')
def aukcja():
    page = request.args.get('page', 1, type=int)
    products = Product.query.paginate(page=page, per_page=9)
    return render_template('aukcja.html', products=products.items, pagination=products)


@app.route('/dodaj_produkt', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        image_file = form.image.data
        image_filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.root_path, 'static/assets/img', image_filename)
        image_file.save(image_path)

        product = Product(
            name=form.name.data,
            type=form.type.data,
            price=form.price.data,
            image=image_filename)

        db.session.add(product)
        db.session.commit()

        flash('Produkt został dodany!', 'success')
        return redirect(url_for('aukcja'))
    return render_template('add_product.html', form=form)


# Helper function to initialize cart in session
def initialize_cart():
    if 'cart' not in session:
        session['cart'] = []


@app.route("/add_to_cart/<int:product_id>")
@login_required
def add_to_cart(product_id):
    initialize_cart()
    product = Product.query.get_or_404(product_id)
    cart = session['cart']

    # Check if the product is already in the cart
    for item in cart:
        if item['id'] == product.id:
            item['quantity'] += 1
            break
    else:
        cart.append({'id': product.id, 'name': product.name, 'price': str(product.price), 'image': product.image,
                     'quantity': 1})

    session['cart'] = cart
    flash('Product added to cart!', 'success')
    return redirect(url_for('view_cart'))


@app.route("/cart", methods=['GET', 'POST'])
@login_required
def view_cart():
    initialize_cart()
    cart = session['cart']
    total_amount = sum(float(item['price']) * item['quantity'] for item in cart)

    if request.method == 'POST':
        # Handle payment processing here
        flash('Payment processed successfully!', 'success')
        session['cart'] = []  # Clear the cart after successful payment
        return redirect(url_for('home'))

    return render_template('cart.html', cart=cart, total_amount=total_amount)


@app.route("/update_cart/<int:product_id>", methods=['POST'])
@login_required
def update_cart(product_id):
    initialize_cart()
    data = request.get_json()
    new_quantity = data['quantity']

    cart = session['cart']
    for item in cart:
        if item['id'] == product_id:
            item['quantity'] = int(new_quantity)
            break

    session['cart'] = cart
    return jsonify({'success': True})


@app.route("/forum")
def forum():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("forum.html", all_posts=posts, current_user=current_user)


# Add a POST method to be able to post comments
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    # Add the CommentForm to the route
    comment_form = CommentForm()
    # Only allow logged-in users to comment on posts
    if comment_form.validate_on_submit():
        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", post=requested_post, current_user=current_user, form=comment_form)


# Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('forum'))


@app.route("/dodaj_post", methods=['GET', 'POST'])
@login_required
def make_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        image_file = form.image.data
        image_filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.root_path, 'static/assets/img', image_filename)
        image_file.save(image_path)

        new_post = BlogPost(
            title=form.title.data,
            body=form.body.data,
            image=image_filename,  # Use the filename here
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )

        db.session.add(new_post)
        db.session.commit()

        flash('Nowy post został dodany!', 'success')
        return redirect(url_for("forum"))
    return render_template("make_post.html", form=form, current_user=current_user)


@app.route("/profil")
@login_required
def profil():
    user = current_user
    posts = BlogPost.query.filter_by(author_id=user.id).all()
    orders = Order.query.filter_by(user_id=user.id).all()
    return render_template("profil.html", user=user, posts=posts, orders=orders)



@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        # Check if user email is already present in the database.
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("Twoje konto już istnieje, przejdź do logowania.")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        # This line will authenticate the user with Flask-Login
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        # Email doesn't exist
        if not user:
            flash("Ten email nie istnieje, spróbuj ponownie.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Hasło jest niepoprawne, spróbuj ponownie.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)


if __name__ == "__main__":
    app.run(debug=True)
