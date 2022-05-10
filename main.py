from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, login_manager, login_required, current_user, logout_user,LoginManager
from forms import CreatePostForm,RegisterForm,LoginForm,CommentForm,OtpForm
from flask_gravatar import Gravatar
from functools import wraps
from flask import abort
import os
from funcs import *

# defining an empty dict to store user info and pass it to the otp_authentication function
user_info={}
flag=True
generated_otp=""

app = Flask(__name__)
app.config['SECRET_KEY'] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
ckeditor = CKEditor(app)
Bootstrap(app)
loginmanager=LoginManager()
loginmanager.init_app(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)
##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##CONFIGURE TABLES

class User(UserMixin,db.Model):
    __tablename__="users"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))
    email=db.Column(db.String(100),unique=True)
    password = db.Column(db.String(100))
    #connection to blogposts table
    posts=relationship("BlogPost",back_populates="author")
    #connection to the comment table
    comments=relationship("Comments",back_populates="commenter")
db.create_all()

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"),nullable=False)
    #connection to the Users table
    author = relationship("User", back_populates="posts")
    #connection to the comments table
    comments = relationship("Comments", back_populates="post")
db.create_all()

class Comments(db.Model):
    __tablename="comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    #foreign key for blogposts
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"),nullable=False)
    #foreign key for Users
    commenter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    #connection to the user Table
    commenter=relationship("User",back_populates="comments")
    #connection to the Blogpost table
    post =relationship("BlogPost", back_populates="comments")
db.create_all()




@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register',methods=['GET','POST'])
def register():
    form=RegisterForm()
    if request.method=="POST":
        if form.validate_on_submit:
            hashed_salted_password=generate_password_hash(form.password.data,
                method='pbkdf2:sha256',
                salt_length=8)
            name=form.name.data
            email=form.email.data
            password=hashed_salted_password
            #storing this values in a global dictionary so that we van acces this dict from the otp authenticate func
            user_info["name"]=name
            user_info["email"]=email
            user_info["password"]=password

            #otp_generated=generate_otp()
            # entered_otp=request.form.get("otp")
            return redirect(url_for('otp_authentication'))
    return render_template("register.html",form=form)

@app.route('/otp',methods=['GET','POST'])
def otp_authentication():
    # if request.method!='POST':
    form = OtpForm()

    while(True):
        global flag,generated_otp
        if flag==False:
            break
        # storing the otp in a variable called generated_otp
        generated_otp=generate_otp()
        print("otp_generated function is executed and the value is",generated_otp)
        flag=False
    print("The value of the generated otp after coming out of the loop is",generated_otp)


    if request.method=="GET":
        #print(generated_otp)
        # print(user_info["email"])
        send_otp(user_info["email"], generated_otp)
    elif request.method=="POST":
        print("during post the value of the generated otp is",generated_otp)
        if form.validate_on_submit():
            entered_otp=form.otp.data
            print("The generated otp is",generated_otp,type(generated_otp))
            print("The entered otp is ",entered_otp,type(entered_otp))
            if entered_otp==generated_otp:
                new_user=User(name=user_info["name"],email=user_info["email"],password=user_info["password"])
                db.session.add(new_user)
                db.session.commit()
                user_info.clear()
                return redirect(url_for('success'))
            elif entered_otp!=generated_otp:
                flash("The Entered OTP is invalid please try again :(")
    return render_template("otp.html",form=form)

@app.route('/success',methods=['GET','POST'])
def success():
    return render_template("success.html")


@loginmanager.user_loader
def user_loader(user_id):
    return User.query.get(int(user_id))


@app.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    if request.method=='POST':
        if form.validate_on_submit():
            mail=form.email.data
            password=form.password.data
            hashed_salted_password = generate_password_hash(password,
                                                            method='pbkdf2:sha256',
                                                            salt_length=8)
            user=User.query.filter_by(email=mail).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('get_all_posts'))


    return render_template("login.html",form=form)


@app.route('/logout')
def logout():
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=['GET','POST'])
def show_post(post_id):
    form=CommentForm()
    requested_post = BlogPost.query.get(post_id)
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.","error")
            print("flash done")
            return redirect(url_for('login'))
        new_comment=Comments(
            text=form.comment_text.data,
            commenter=current_user,
            post=requested_post,
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post',post_id=post_id))
    return render_template("post.html", post=requested_post,form=form)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


#admin only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if not current_user.is_authenticated or current_user.id!=1:
            return abort(403)
        else:
            return f(*args,**kwargs)
    return decorated_function

@app.route("/new-post",methods=['GET','POST'])
@login_required
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        print(current_user.id)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>",methods=['GET','POST'])
@login_required
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@login_required
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000,debug=True)
