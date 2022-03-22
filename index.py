from flask import Flask, render_template, request, flash, session, url_for, redirect
import requests
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


class Ratings(db.Model):
    __tablename__ = "ratings"

    rating_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.user_id))
    movie_id = db.Column(db.Integer)
    rating_score = db.Column(db.Integer)

    def __repr__(self):
        return f"User {self.user_id} rated {self.rating_score}"


class Reviews(db.Model):
    __tablename__ = "reviews"

    review_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.user_id))
    movie_id = db.Column(db.Integer)
    rating_id = db.Column(db.Integer, db.ForeignKey(Ratings.rating_id))
    review = db.Column(db.Text)

    def __repr__(self):
        return f"{self.review}"


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
    
    return render_template('movie-info.html', results=results, actors=actors, director=director)





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
            session['email'] = email
            session['name'] = user.user_first_name
            print(session['name'])
        elif user.email == email and not hash(user.password) == password:
            print("Incorrect Password")
        else:
            print("Email not found")
    
    return redirect(url_for('home'))


@app.route('/logout')
def process_logout():
    session.pop('email', None)
    session.pop('name', None)
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

    new_user = User(user_first_name=first_name, user_last_name=last_name, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('home'))



@app.route('/reviews/<movie_id>')
def see_reviews(movie_id):
    reviews = Reviews.query.all()
    review_list = []
    for review in reviews:
        if str(review.movie_id) == str(movie_id):
            review_list.append(review)
    return render_template('reviews.html', reviews=review_list)






if __name__ == '__main__':
    app.run()
