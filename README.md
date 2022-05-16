The Movie Source: your source for everything movies

The Movie Source is a web based application to view information and interact with movies. It uses Python, Flask, Jinja, SQLAlchemy, and a Postgres database to store user information. The features included are:
•	Search for any movie to obtain various information from The Movie Database API.
•	View all reviews that have been left by other users
•	Create an account to access more features.
•	Rate movies on a scale of 1-10.
•	Write your own review for a movie (also provides a rating)
•	Add and delete movies from your personal list.

How does it work?
The Movie Source uses various Python classes, routes, and functions to process different requests such as logging in, viewing movies, writing a review, etc. The information is then displayed on a template HTML page through Flask and Jinja. All information regarding any movie is pulled from The Movie Database API (https://www.themoviedb.org/documentation/api). Usernames, email addresses, and passwords are stored in a Postgres Database that is hosted on Heroku. The password is hashed with the passlib.hash directory before it is stored in the database. All forms are processed with WTForms will additional validators included to ensure they are completed properly.

How to use the app?
The Movie Source is deployed on the Digital Ocean platform at the following URL: https://the-movie-source-4ix3h.ondigitalocean.app/home. All features can be accessed through that link. The repository includes a requirements.txt file for what needs to be installed in order to run the application. Anyone pulling the code from the repository will need to get an API Key from The Movie Database API, create their secret key, as well as be given the link to the PostgreSQL database that is not shared in the push to GitHub.
