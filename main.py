from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from dotenv import load_dotenv
import requests
import os
load_dotenv('.env')


##CREATE SERVER
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


##CREATE DATABASE
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
db = SQLAlchemy()
db.init_app(app)


##CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String, nullable=True)
    img_url = db.Column(db.String, nullable=True)


with app.app_context():
    db.create_all()


##CREATE FORMS
class RateMovieForm(FlaskForm):
    rating = StringField(label="Your rating out of 10 (e.g. 7.5)", validators=[DataRequired()], render_kw={"autocomplete": "off", "autofocus": True})
    review = StringField(label="Your review", validators=[DataRequired()], render_kw={"autocomplete": "off"})
    submit = SubmitField(label="Done")


class FindMovieForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()], render_kw={"autocomplete": "off", "autofocus": True})
    submit = SubmitField(label="Add Movie")


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating.desc()))
    movies = result.scalars().all()
    rank = 1
    for movie in movies:
        movie.ranking = rank
        rank += 1

    return render_template("index.html", movies=movies)


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)

    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    else:
        return render_template("edit.html", movie=movie, form=form)


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = FindMovieForm()

    if form.validate_on_submit():
        movie = form.title.data
        response = requests.get("https://api.themoviedb.org/3/search/movie", params={"api_key": os.getenv('API_KEY'), "query": movie})
        data: list[dict] = response.json()["results"]

        return render_template("select.html", options=data)
    
    else:
        return render_template("add.html", form=form)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/select")
def select_movie():
    movie_id = request.args.get("movie_id")
    response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}", params={"api_key": os.getenv('API_KEY')})
    data = response.json()
    title = data["original_title"]
    img_url = "https://image.tmdb.org/t/p/w500/" + data["poster_path"]
    year = data["release_date"][:4]
    description = data["overview"]

    movie = Movie(
        title=title,
        year=year,
        description=description,
        img_url=img_url,
    )

    db.session.add(movie)
    db.session.commit()

    return redirect(url_for("rate_movie", id=movie.id))


if __name__ == '__main__':
    app.run(debug=True)
