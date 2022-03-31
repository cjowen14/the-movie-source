from flask import Flask, render_template, request, flash, session, url_for, redirect
import requests
import os
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt
from sqlalchemy import create_engine
from pprint import pprint
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, RadioField
from wtforms.validators import DataRequired, Length, email_validator
app = Flask(__name__)
db = SQLAlchemy()

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.app = app
db.init_app(app)

app.secret_key = os.getenv('SECRET_KEY')
api_key = os.getenv('API_KEY')

## GLOBAL VARIABLES
results_list = []
search_results_list = []

## CREATE USER CLASS
class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_first_name = db.Column(db.String(255))
    user_last_name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    password = db.Column(db.String(255))
    def __repr__(self):
        return f"{self.user_first_name} {self.user_last_name}"

## CREATE RATINGS CLASS
class Ratings(db.Model):
    __tablename__ = "ratings"
    rating_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.user_id))
    movie_id = db.Column(db.Integer)
    rating_score = db.Column(db.Integer)
    def __repr__(self):
        return f"User {self.user_id} rated {self.rating_score}"

## CREATE REVIEWS CLASS
class Reviews(db.Model):
    __tablename__ = "reviews"
    review_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.user_id))
    movie_id = db.Column(db.Integer)
    rating_id = db.Column(db.Integer, db.ForeignKey(Ratings.rating_id))
    review = db.Column(db.Text)
    def __repr__(self):
        return f"{self.review}"

## CREATE FAVORITES CLASS
class Favorites(db.Model):
    __tablename__ = "favorites_list"
    favorites_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    movie_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey(User.user_id))
    def __repr__(self):
        return f"User {self.user_id} added {self.movie_id}"

## REGISTRATION FORM CLASS
class RegisterForm(FlaskForm):
    user_first_name = StringField("First Name", validators=[DataRequired("data is required!")])
    user_last_name = StringField("Last Name", validators=[DataRequired("data is required!")])
    email = StringField("Email", validators=[DataRequired("data is required!")])
    password = PasswordField("Password", validators=[DataRequired("data is required!"), Length(min=5, max=20, message="Password must be between 5-20 characters long.")])
    submit = SubmitField("Register")
    def __repr__(self):
        return f"{self.user_first_name} {self.user_last_name} {self.email} {self.password}"

## LOGIN FORM CLASS
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired("data is required!")])
    password = PasswordField("Password", validators=[DataRequired("data is required!")])
    submit = SubmitField("Login")
    def __repr__(self):
        return f"{self.email} {self.password}"

## REVIEW FORM CLASS
class ReviewForm(FlaskForm):
    review = TextAreaField("Review", validators=[DataRequired()])
    ratings = RadioField("", choices=[('1', '1'), ('2', '2'),('3', '3'), ('4', '4'),('5', '5'), ('6', '6'),('7', '7'), ('8', '8'),('9', '9'), ('10', '10')])
    submit = SubmitField("Submit")

## RATING FORM CLASS
class RatingForm(FlaskForm):
    ratings = RadioField("", choices=[('1', '1'), ('2', '2'),('3', '3'), ('4', '4'),('5', '5'), ('6', '6'),('7', '7'), ('8', '8'),('9', '9'), ('10', '10')])
    submit = SubmitField("Submit")


## DISPLAY AND PROCESS LOGIN, LOGOUT, AND REGISTRATION
@app.route('/login', methods=['GET', 'POST'])
def show_login():
    form = LoginForm()
    if request.method == 'GET':
        return render_template('login.html', form=form)
    if form.validate_on_submit:
        email = form.email.data
        password = form.password.data
        users = User.query.all()
        for user in users:
            if user.email == email and sha256_crypt.verify(password, user.password):
                flash(f"Welcome back {user.user_first_name}!")
                session['id'] = user.user_id
                session['email'] = email
                session['name'] = user.user_first_name
                return redirect(url_for('home'))
            elif user.email == email and not sha256_crypt.encrypt(user.password) == password:
                flash("Incorrect Password")
                return redirect(url_for('show_login'))
            
        flash("Email not found")        
        return redirect(url_for('show_login'))

@app.route('/logout')
def process_logout():
    session.pop('email', None)
    session.pop('name', None)
    session.pop('id', None)
    flash("You have been successfully logged out!")
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def show_register():
    form = RegisterForm()
    if request.method == 'GET':
        return render_template('register.html', form=form)
    if form.validate_on_submit():
        first_name = form.user_first_name.data
        last_name = form.user_last_name.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        users = User.query.all()
        for u in users:
            if email == u.email:
                flash("Email already exists")
                return redirect(url_for('show_register'))
        new_user = User(user_first_name=first_name, user_last_name=last_name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash(f"Welcome {first_name}!!")
        session['id'] = new_user.user_id
        session['email'] = email
        session['name'] = new_user.user_first_name
        return redirect(url_for('home'))
    else:
        flash("{}".format(form.errors), "danger")
        return render_template("register.html")


## GET POPULAR MOVIES AND DISPLAY ON HOME PAGE
@app.route('/', methods=["GET"])
@app.route('/home', methods=["GET"])
def home():
    ## GET 10 PAGES OF POPULAR MOVIES
    page = 1
    global results_list
    results_list = []
    while page <= 10:
        api_res = requests.get(f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=en-US&page={page}").json()['results']
        results_list.append(api_res)
        page += 1
    ## TRIM TITLE TO FIT ON ONE LINE
    s = slice(0,23)
    for movie in results_list[0]:
        if len(movie['title'])>24:
            movie['title'] = movie['title'][s] + '..'
    return render_template('home.html', results=results_list[0], page=1)


## PROCESS NEXT OR PREVIOUS PAGE OF POPULAR MOVIES
@app.route('/home-<page>')
def next_page(page):
    s = slice(0,23)
    for movie in results_list[int(page) - 1]:
        if len(movie['title'])>24:
            movie['title'] = movie['title'][s] + '..'
    return render_template('home.html', results=results_list[int(page) - 1], page=int(page))


## PROCESS SEARCH RESULTS FOR EACH POSSIBLE PAGE
@app.route('/', methods=["POST"])
@app.route('/home', methods=["POST"])
def search_results():
    user_search = request.form['search']
    return redirect(url_for('search_results2',user_search=user_search))

@app.route('/movie-info/<movie_id>', methods=["POST"])
def search_results_B(movie_id):
    user_search = request.form['search']
    return redirect(url_for('search_results2',user_search=user_search))

@app.route('/search-results/<user_search>', methods=["POST"])
def search_results_C(user_search):
    user_search = request.form['search']
    return redirect(url_for('search_results2',user_search=user_search))


## DISPLAY SEARCH RESULTS
@app.route('/search-results/<user_search>')
def search_results2(user_search):
    global search_results_list
    search_results_list = []
    pages = int(requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&language=en-US&page=1&include_adult=false&query={user_search}").json()['total_pages'])
    counter = 1
    while counter <= pages:
        api_res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&language=en-US&page={counter}&include_adult=false&query={user_search}").json()['results']
        search_results_list.append(api_res)
        counter += 1
    ## TRIM TITLE TO FIT ON ONE LINE
    s = slice(0,23)
    for movie in search_results_list[0]:
        if len(movie['title'])>24:
            movie['title'] = movie['title'][s] + '..'
    return render_template('search-results.html', user_search=user_search, results=search_results_list[0], page=1, total_pages=pages)


## PROCESS NEXT OR PREVIOUS PAGE OF SEARCH RESULTS
@app.route('/search-results/<user_search>-<page>-<total_pages>')
def next_search(user_search, page, total_pages):
    s = slice(0,23)
    for movie in search_results_list[int(page) - 1]:
        if len(movie['title'])>24:
            movie['title'] = movie['title'][s] + '..'
    return render_template('search-results.html', user_search=user_search, results=search_results_list[int(page) - 1], page=int(page), total_pages=int(total_pages))


## SHOW MOVIE INFORMATION
@app.route('/movie-info/<movie_id>')
def movie_info(movie_id):
    ## GET MOVIE INFORMATION
    api_res = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}")
    results = api_res.json()
    api_cred = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={api_key}")
    credits = api_cred.json()
    ## GET ACTORS FROM CREDITS
    actors = []
    x = 1
    for actor in credits['cast']:
        if x <=7:
            actors.append(actor['name'])
            x+=1
    ## GET DIRECTOR FROM CREDITS
    director = []
    for person in credits['crew']:
        if person['department'] == 'Directing':
            director.append(person['name'])
    ## GET STREAMING SERVICES
    api_res = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={api_key}").json()
    try:
        stream = api_res['results']['US']['flatrate']
    except:
        stream = []
    ## GET LIST OF FAVORITES, CHECK TO SEE IF MOVIE IS IN USER'S LIST, CHECK TO SEE IF USER HAS RATED AND REVIEWED MOVIE
    favorites = Favorites.query.all()
    ratings = Ratings.query.all()
    reviews = Reviews.query.all()
    user_rating = 0
    favorited = 0
    reviewed = 0
    if session:
        for rating in ratings:
            if str(rating.user_id) == str(session['id']) and str(rating.movie_id) == str(movie_id):
                user_rating = int(rating.rating_score)
        for fav in favorites:
            if str(fav.movie_id) == str(movie_id) and str(fav.user_id) == str(session['id']):
                favorited = movie_id
        for review in reviews:
            if str(review.movie_id) == str(movie_id) and str(review.user_id) == str(session['id']):
                reviewed = movie_id
    return render_template('movie-info.html', results=results, actors=actors, director=director, favorites=favorited, stream=stream, user_rating=user_rating, review=reviewed)


## VIEW ALL REVIEWS FOR MOVIE
@app.route('/reviews/<movie_id>')
def see_reviews(movie_id):
    reviews = Reviews.query.all()
    users = User.query.all()
    review_dict = {}
    final_dict = {}
    api_res = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}")
    movie = api_res.json()
    ##  GET REVIEWS FOR MOVIE
    for review in reviews:
        if str(review.movie_id) == str(movie_id):
            review_dict[review.user_id] = review.review
    ## GET USER NAMES ASSOCIATED WITH EACH REVIEW
    for review in review_dict:
        for user in users:
            if review == user.user_id:
                final_dict[user.user_first_name + " " + user.user_last_name] = review_dict[review]
    return render_template('reviews.html', reviews=final_dict, movie=movie)


## WRITE REVIEW FOR MOVIE
@app.route('/write-review/<movie_id>', methods=["GET", "POST"])
def write_review(movie_id):
    form = ReviewForm()
    reviews = Reviews.query.all()
    ratings = Ratings.query.all()
    if request.method == "GET":
        api_res = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}")
        movie = api_res.json()
        for review in reviews:
            if str(review.movie_id) == str(movie_id) and str(review.user_id) == str(session['id']):
                form.review.data = review.review
                form.submit.label.text = "Update"
        return render_template('write-review.html', movie=movie, form=form)
    new_review = form.review.data
    new_rating = form.ratings.data
    for r in reviews:
        if str(r.movie_id) == str(movie_id) and str(r.user_id) == str(session['id']):
            r.review = new_review
            db.session.commit()
            for rate in ratings:
                if str(rate.movie_id) == str(movie_id) and str(rate.user_id) == str(session['id']):
                    rate.rating_score = new_rating
                    db.session.commit()
            return redirect(url_for('see_reviews',movie_id=movie_id))
    new_rating = Ratings(user_id=session['id'], movie_id=movie_id, rating_score=new_rating)
    db.session.add(new_rating)
    db.session.commit()
    new_review = Reviews(user_id=session['id'], movie_id=movie_id, rating_id=new_rating.rating_id, review=new_review)
    db.session.add(new_review)
    db.session.commit()
    return redirect(url_for('see_reviews',movie_id=movie_id))



## ADD THE RATING TO THE DB
@app.route('/rate-movie/<movie_id>', methods=["GET", "POST"])
def submit_rating(movie_id):
    form = RatingForm()
    ratings = Ratings.query.all()
    if request.method == 'GET':
        api_res = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}")
        movie = api_res.json()
        form.submit.label.text = "Update"
        return render_template('rate.html', movie=movie, form=form)
    new_rating = form.ratings.data
    for rate in ratings:
        if str(rate.movie_id) == str(movie_id) and str(rate.user_id) == str(session['id']):
            rate.rating_score = new_rating
            db.session.commit()
            return redirect(url_for('movie_info', movie_id=movie_id))
    new_rating = Ratings(user_id=session['id'], movie_id=movie_id, rating_score=new_rating)
    db.session.add(new_rating)
    db.session.commit()
    return redirect(url_for('movie_info', movie_id=movie_id))


## ADD MOVIE TO FAVORITES LIST
@app.route('/fav-list/<movie_id>')
def add_fav(movie_id):
    new_fav = Favorites(movie_id=movie_id, user_id=session['id'])
    db.session.add(new_fav)
    db.session.commit()
    return redirect(url_for('your_list'))

## REMOVE MOVIE FROM FAVORITES LIST
@app.route('/delete-fav/<movie_id>')
def del_fav(movie_id):
    del_fav = Favorites.query.filter_by(movie_id=movie_id).first()
    db.session.delete(del_fav)
    db.session.commit()
    return redirect(url_for('your_list'))


## VIEW ALL USER'S RATINGS
@app.route('/your-ratings')
def your_ratings():
    ratings = Ratings.query.all()
    results = {}
    titles={}
    for rating in ratings:
        if rating.user_id == session['id']:
            movie = rating.movie_id
            results[movie] = rating.rating_score
    for movie in results:
        title = requests.get(f"https://api.themoviedb.org/3/movie/{movie}?api_key={api_key}&language=en-US").json()['title']
        titles[title] = results[movie]
    return render_template('your-ratings.html', titles=titles)


## VIEW ALL USER'S REVIEWS
@app.route('/your-reviews')
def your_reviews():
    reviews= Reviews.query.all()
    results = {}
    titles={}
    for review in reviews:
        if review.user_id == session['id']:
            movie = review.movie_id
            results[movie] = review.review
    for movie in results:
        title = requests.get(f"https://api.themoviedb.org/3/movie/{movie}?api_key={api_key}&language=en-US").json()['title']
        titles[title] = results[movie]
    return render_template('your-reviews.html', titles=titles)


## VIEW USER'S LIST
@app.route('/your-list')
def your_list():
    favorites = Favorites.query.all()
    list = []
    for movie in favorites:
        if movie.user_id == session['id']:
            fav = requests.get(f"https://api.themoviedb.org/3/movie/{movie.movie_id}?api_key={api_key}&language=en-US").json()
            list.append(fav)
    s = slice(0,23)
    for movie in list:
        if len(movie['title'])>24:
            movie['title'] = movie['title'][s] + '..'
    return render_template('your-list.html', movies=list)





if __name__ == '__main__':
    app.run()
