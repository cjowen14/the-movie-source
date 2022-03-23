from flask import Flask, render_template, request, flash, session, url_for, redirect
import requests
import os
from flask_sqlalchemy import SQLAlchemy
import secret
import psycopg2
app = Flask(__name__)
db = SQLAlchemy()

app.config['SQLALCHEMY_DATABASE_URI'] = secret.uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.app = app
db.init_app(app)

app.secret_key = secret.secret_key
api_key = secret.api_key

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


## DISPLAY AND PROCESS LOGIN, LOGOUT, AND REGISTRATION
@app.route('/login')
def show_login():
    return render_template('login.html')

@app.route('/login', methods=["POST"])
def process_login():
    email = request.form['email']
    password = hash(request.form['password'])
    users = User.query.all()
    for user in users:
        if user.email == email and hash(user.password) == password:
            print("You are logged in!")
            session['id'] = user.user_id
            session['email'] = email
            session['name'] = user.user_first_name
            return redirect(url_for('home'))
        elif user.email == email and not hash(user.password) == password:
            print("Incorrect Password")
            return redirect(url_for('show_login'))
        
    print("Email not found")        
    return redirect(url_for('show_login'))

@app.route('/logout')
def process_logout():
    session.pop('email', None)
    session.pop('name', None)
    session.pop('id', None)
    return redirect(url_for('home'))

@app.route('/register')
def show_register():
    return render_template('register.html')

@app.route('/register', methods=["POST"])
def process_register():
    first_name = request.form['first']
    last_name = request.form['last']
    email = request.form['email']
    password = request.form['password']
    users = User.query.all()
    for u in users:
        if email == u.email:
            print("Email already exists")
            return redirect(url_for('show_register'))
    new_user = User(user_first_name=first_name, user_last_name=last_name, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('home'))


## GET POPULAR MOVIES AND DISPLAY ON HOME PAGE
@app.route('/', methods=["GET"])
@app.route('/home', methods=["GET"])
def home():
    api_res = requests.get(f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=en-US&page=1")
    results = api_res.json()['results']
    ## TRIM TITLE TO FIT ON ONE LINE
    s = slice(0,24)
    for movie in results:
        if len(movie['title'])>25:
            movie['title'] = movie['title'][s] + '..'
    return render_template('home.html', results=results)


## PROCESS SEARCH RESULTS FOR EACH POSSIBLE PAGE
@app.route('/', methods=["POST"])
@app.route('/home', methods=["POST"])
def search_results():
    user_search = request.form['search']
    return redirect(url_for('search_results2',user_search=user_search))

# @app.route('/movie-info/<movie_id>', methods=["POST"])
# def search_results_B(movie_id):
#     user_search = request.form['search']
#     return redirect(url_for('search_results2',user_search=user_search))

@app.route('/search-results/<user_search>', methods=["POST"])
def search_results_C(user_search):
    user_search = request.form['search']
    return redirect(url_for('search_results2',user_search=user_search))


## DISPLAY SEARCH RESULTS
@app.route('/search-results/<user_search>')
def search_results2(user_search):
    api_res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&language=en-US&page=1&include_adult=false&query={user_search}")
    results = api_res.json()['results']
    ## TRIM TITLE TO FIT ON ONE LINE
    s = slice(0,24)
    for movie in results:
        if len(movie['title'])>25:
            movie['title'] = movie['title'][s] + '..'
    return render_template('search-results.html', user_search=user_search, results=results)


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
        buy = api_res['results']['US']['buy']
    except:
        buy = []
    try:
        rent = api_res['results']['US']['rent']
    except:
        rent = []
    try:
        stream = api_res['results']['US']['flatrate']
    except:
        stream = []
    
    ## GET LIST OF FAVORITES AND CHECK TO SEE IF MOVIE IS IN USER'S LIST
    favorites = Favorites.query.all()
    favorited = 0
    for fav in favorites:
        if str(fav.movie_id) == str(movie_id):
            favorited = movie_id
            return render_template('movie-info.html', results=results, actors=actors, director=director, favorites=favorited, buy=buy, rent=rent, stream=stream)
    return render_template('movie-info.html', results=results, actors=actors, director=director, favorites=favorited, buy=buy, rent=rent, stream=stream)


## VIEW ALL REVIEWS FOR MOVIE
@app.route('/reviews/<movie_id>')
def see_reviews(movie_id):
    reviews = Reviews.query.all()
    review_list = []
    for review in reviews:
        if str(review.movie_id) == str(movie_id):
            review_list.append(review)
    return render_template('reviews.html', reviews=review_list)


## WRITE REVIEW FOR MOVIE
@app.route('/write-review/<movie_id>', methods=["GET"])
def write_review(movie_id):
    api_res = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}")
    movie = api_res.json()
    return render_template('write-review.html', movie=movie)


## ADD REVIEW TO DATABASE
@app.route('/write-review/<movie_id>', methods=["POST"])
def submit_review(movie_id):
    review = request.form['review']
    rating = request.form['rating']
    new_rating = Ratings(user_id=session['id'], movie_id=movie_id, rating_score=rating)
    db.session.add(new_rating)
    db.session.commit()
    new_review = Reviews(user_id=session['id'], movie_id=movie_id, rating_id=new_rating.rating_id, review=review)
    db.session.add(new_review)
    db.session.commit()
    return redirect(url_for('see_reviews',movie_id=movie_id))


## GIVE JUST A RATING FOR A MOVIE
@app.route('/rate-movie/<movie_id>', methods=["GET"])
def rate_movie(movie_id):
    return render_template('rate.html')


## ADD THE RATING TO THE DBpyt
@app.route('/rate-movie/<movie_id>', methods=["POST"])
def submit_rating(movie_id):
    rating = request.form['rating']
    new_rating = Ratings(user_id=session['id'], movie_id=movie_id, rating_score=rating)
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
    s = slice(0,24)
    for movie in list:
        if len(movie['title'])>25:
            movie['title'] = movie['title'][s] + '..'
    return render_template('your-list.html', movies=list)





if __name__ == '__main__':
    app.run()
