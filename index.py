from flask import Flask, render_template, request, flash, session, url_for, redirect
import requests
from flask_sqlalchemy import SQLAlchemy
import secret
app = Flask(__name__)
db = SQLAlchemy()

api_key = secret.api_key


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

@app.route('/register', methods=["POST"])
def search_results_D():
    user_search = request.form['search']
    return redirect(url_for('search_results2',user_search=user_search))

@app.route('/login', methods=["POST"])
def search_results_E():
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

@app.route('/register')
def show_register():
    return render_template('register.html')


