import profile
from unicodedata import name
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField , SubmitField, PasswordField, BooleanField, ValidationError, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length
from flask_wtf.file import FileField
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid as uuid
from wtforms.widgets import TextArea
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_ckeditor import CKEditor
from flask_ckeditor import CKEditorField
import os

app = Flask(__name__)
ckeditor = CKEditor(app)

#create database (This is a new db)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:PASSword123@localhost/users'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:PASSword123@localhost/blog'

#create a heroku database for deployment postgresql
app.config['SQLALCHEMY_DATABASE_URI'] =  'postgres://gfntgvspykdgfn:2a680a3255e7ba55cc2deb89898cfc6b0e1018ca1acc7e14f3a9a5bbbc9eefe4@ec2-54-173-237-110.compute-1.amazonaws.com:5432/d2bdjag779666c'

#create a seceret key for wtforms
app.config['SECRET_KEY'] = 'my secret key is my name'

#saving profile picture
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#initialize database
db = SQLAlchemy(app)

#initialize migration
migrate = Migrate(app, db)

#initialize flask-login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#user loader
@login_manager.user_loader  
def load_user(user_id):
    return Users.query.get(int(user_id))

#create a database model(sqlite and mysql)
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(200), nullable=False, unique=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
    phone_number = db.Column(db.String(200), nullable=False)
    about_author = db.Column(db.Text(), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    profile_pic = db.Column(db.String(200), nullable=True)
    #Hash password
    password_hash = db.Column(db.String(128))    
    #user can have many blogs
    blogs = db.relationship('Blog', backref='users')


    #Add password property
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    #Add password setter
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    #Add password verification
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<Name %r>' % self.name

#create a form for the database
class UserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    about_author = TextAreaField('About Author', validators=[DataRequired()])
    password_hash = PasswordField('Password', validators=[DataRequired(), EqualTo('password_hash1', message='Passwords Must Match!')])
    password_hash1 = PasswordField('Re-Enter Your Password', validators=[DataRequired()])
    profile_pic = FileField('Profile Picture')
    submit = SubmitField('Submit')

#Create a model the database for blog
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    slug = db.Column(db.String(100), nullable=False)
    #foreign key is link to the user table(primary key)
    bloger_id = db.Column(db.Integer, db.ForeignKey('users.id'))

#create form for blog
class BlogForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = CKEditorField('Content', validators=[DataRequired()], widget=TextArea())
    slug = StringField('Slug', validators=[DataRequired()])
    submit = SubmitField('Submit')

# create a form class for login page
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

#create form for search
class SearchForm(FlaskForm):
    searched = StringField('Searched', validators=[DataRequired()])
    submit = SubmitField('Search')

#create a deafult route
@app.route('/')
def index():
    return render_template('index.html')

#create a route for admain page
@app.route('/admin')
@login_required
def admin():
    id = current_user.id
    if id == 1:
        return render_template('admin.html')
    else:
        flash('You are not allowed to access this page')
        return redirect(url_for('dashboard'))


#create a database route
@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            #create a hash password
            hashed_pwd = generate_password_hash(form.password_hash.data, method='sha256')            
            user = Users(name=form.name.data, username=form.username.data ,email=form.email.data, phone_number=form.phone_number.data, 
            password_hash=hashed_pwd)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.email.data = ''
        form.username.data = ''
        form.phone_number.data = ''
        form.password_hash.data = ''
        flash(f'User { name } added successfully! ')
    our_users = Users.query.order_by(Users.date_added).all()    
    return render_template('add_user.html', form=form, name=name, our_users=our_users)

#create a database update route
@app.route('/user/update/<int:id>', methods=['GET', 'POST'])
def user_update(id):
    users_to_update = Users.query.get_or_404(id)
    form = UserForm()
    if request.method == 'POST':
        users_to_update.name = request.form['name']
        users_to_update.email = request.form['email']
        users_to_update.username = request.form['username']
        users_to_update.phone_number = request.form['phone_number']
        users_to_update.about_author = request.form['about_author']
        users_to_update.profile_pic = request.files['profile_pic']
        #create a file name for profile picture
        profile_pic_filename = secure_filename(users_to_update.profile_pic.filename)#form.profile_pic.data.filename
        #create a random file name for profile picture
        pic_name = str(uuid.uuid1()) + "_" + profile_pic_filename
        #save the profile picture
        users_to_update.profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
        users_to_update.profile_pic = pic_name
        try:                
            db.session.commit()
            flash(f'User { users_to_update.name } updated successfully! ')  
            our_users = Users.query.order_by(Users.date_added).all()         
            return render_template('user_update.html', form=form, users_to_update=users_to_update, our_users=our_users)
        except:
            flash(f'User { users_to_update.name } was not updated!, please try again! ')
            our_users = Users.query.order_by(Users.date_added).all()
            return render_template('user_update.html', form=form, users_to_update=users_to_update, our_users=our_users)
    else:
        # form.name.data = user.name
        # form.email.data = user.email
        our_users = Users.query.order_by(Users.date_added).all()
        return render_template('user_update.html', form=form, users_to_update=users_to_update, our_users=our_users, id=id)

#create a database delete route
@app.route('/user/delete/<int:id>')
def user_delete(id):
    user_to_delete = Users.query.get_or_404(id)
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'User { user_to_delete.name } deleted successfully! ')
        return redirect(url_for('add_user'))
    except:
        flash(f'User { user_to_delete.name } was not deleted!, please try again! ')
        return redirect(url_for('add_user'))

#add blog post route
@app.route('/blog/add', methods=['GET', 'POST'])
# @login_required
def add_blog():
    form = BlogForm()
    title = None

    if form.validate_on_submit():
        users = current_user.id
        blogs = Blog(title=form.title.data, bloger_id=users, content=form.content.data, slug=form.slug.data)
        title = form.title.data
        form.title.data = ''
        form.content.data = ''
        form.slug.data = ''
        db.session.add(blogs)
        db.session.commit()
        flash(f'Blog { title } added successfully! ')
    return render_template('add_blog.html', form=form, title=title)

#create a database delete route for blog
@app.route('/blog/delete/<int:id>')
@login_required
def blog_delete(id):
    blog_to_delete = Blog.query.get_or_404(id)
    id = current_user.id
    if id == blog_to_delete.users.id:
        try:
            db.session.delete(blog_to_delete)
            db.session.commit()
            flash(f'Blog { blog_to_delete.title } deleted successfully! ')
            return redirect(url_for('blog_posts'))
        except:
            flash(f'Blog { blog_to_delete.title } was not deleted!, please try again! ')
            return redirect(url_for('blog_posts'))
    else:
        flash(f'Blog { blog_to_delete.title } was not deleted!, you are not the owner of this blog! ')
        return redirect(url_for('blog_posts'))

#create a route for all blog post view
@app.route('/blog/posts')
# @login_required
def blog_posts():
    our_blogs = Blog.query.order_by(Blog.date_posted).all()
    return render_template('blog_posts.html', our_blogs=our_blogs)

#create a route for single blog post view
@app.route('/blog/post/<int:id>')
def blog_post(id):
    blog = Blog.query.get_or_404(id)
    return render_template('blog_post.html', blog=blog)

#create a route for updating blog post
@app.route('/blog/update/<int:id>', methods=['GET', 'POST'])
@login_required
def blog_update(id):
    title = None
    blog_to_update = Blog.query.get_or_404(id)
    form = BlogForm()
    if request.method == 'POST':
        blog_to_update.title = request.form['title']
        blog_to_update.content = request.form['content']
        blog_to_update.slug = request.form['slug']               
        db.session.commit()
        flash(f'Blog { blog_to_update.title } updated successfully! ')  
        return redirect(url_for('blog_post', id=blog_to_update.id))
    if current_user.id == blog_to_update.users.id:
        title = form.title.data
        form.title.data = blog_to_update.title
        form.content.data = blog_to_update.content
        form.slug.data = blog_to_update.slug
        return render_template('blog_update.html', form=form, blog_to_update=blog_to_update, title=title)
    else:
        flash(f'Blog { blog_to_update.title } was not updated!, you are not the owner of this blog! ')
        return redirect(url_for('blog_posts', id=blog_to_update.id))

#create route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash(f'Welcome { user.name }! You are now logged in! ')
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect password, please try again!')
        else:
            flash('Username does not exist, please try again!')
    return render_template('login.html', title='Sign In', form=form)

#create route for logout page
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You are now logged out!')
    return redirect(url_for('login'))

#create route for dashboard page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')

#create setter for search page
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

#create route for search page
@app.route('/search', methods=['POST'])
def search():
    form = SearchForm()
    blogs = Blog.query
    if form.validate_on_submit():
        # Get data from submitted form
        blogs.searched = form.searched.data
        # Query the Database
        blogs = blogs.filter(Blog.content.like('%' + blogs.searched + '%'))
        blogs = blogs.order_by(Blog.title).all()

        return render_template("search.html",
            form=form,
            # searched = blogs.searched,
            blogs = blogs)

#create error handler route
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#create error handler route for 500
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)