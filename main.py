from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests


MOVIE_DB_KEY = "78c3b16a28fb30a5b80b1cd82bdb29eb"
MOVIE_DB_ENDPOINT = "https://api.themoviedb.org/3/"
MOVIE_DB_IMAGE_URL_BASE = "https://image.tmdb.org/t/p/original/"


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///films.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)


class Film(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    title = db.Column("title", db.String(60), unique=True, nullable=False)
    year = db.Column("year", db.String(4))
    description = db.Column("description", db.String(300))
    rating = db.Column("rating", db.String(10))
    ranking = db.Column("ranking", db.String(10))
    review = db.Column("review", db.String(300))
    img_url = db.Column("img_url", db.String(300), unique=True)

    def __repr__(self):
        return '<Title %r>' % self.title


class FilmSearchForm(FlaskForm):
    title = StringField(label="Film Title", validators=[DataRequired()])
    submit = SubmitField(label="Search")


class FilmEditForm(FlaskForm):
    rating = StringField(label="Your Rating out of 10 e.g 7.5", validators=[DataRequired()])
    review = StringField(label="Your Review", validators=[DataRequired()])
    submit = SubmitField(label="Done")


@app.route("/")
def home():
    all_films = db.session.query(Film).order_by(Film.rating.asc())
    film_count = all_films.count()
    for index, film in enumerate(all_films):
        film.ranking = film_count - index
    return render_template("index.html", films=all_films)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    edit_form = FilmEditForm()
    film_to_update = Film.query.get(id)
    if edit_form.validate_on_submit():
        film_to_update.rating = edit_form.rating.data
        film_to_update.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    else:
        return render_template("edit.html", form=edit_form, film=film_to_update)


@app.route("/add", methods=["GET", "POST"])
def add():
    film_form = FilmSearchForm()
    if film_form.validate_on_submit():
        film_title = film_form.title.data
        params = {
            "api_key": MOVIE_DB_KEY,
            "query": film_title
        }
        films_data = requests.get(url=MOVIE_DB_ENDPOINT + "search/movie", params=params).json()["results"]
        return render_template("select.html", films=films_data)
    else:
        return render_template("add.html", form=film_form)


@app.route("/select/<int:film_id>")
def select(film_id):
    film_data = requests.get(url=MOVIE_DB_ENDPOINT + f"movie/{film_id}", params={"api_key": MOVIE_DB_KEY}).json()
    print(film_data)
    film_title = film_data["title"]
    release_year = film_data["release_date"].split("-")[0]
    description = film_data["overview"]
    img_path = f"{MOVIE_DB_IMAGE_URL_BASE}{film_data['poster_path']}"

    new_film = Film(
        title=film_title,
        year=release_year,
        description=description,
        img_url=img_path
    )
    db.session.add(new_film)
    db.session.commit()

    return redirect(url_for("edit", id=new_film.id))


@ app.route("/delete/<int:id>")
def delete(id):
    film_to_delete = Film.query.get(id)
    db.session.delete(film_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)
