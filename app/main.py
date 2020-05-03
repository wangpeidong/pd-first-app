print(f"__file__={__file__:<35} | __name__={__name__:<20} | __package__={str(__package__):<20}")

from flask import Flask, request, jsonify, render_template, flash, redirect, url_for, session
from passlib.hash import sha256_crypt
import bs4 as bs
import urllib.request
import gc

app = Flask(__name__)
app.secret_key = b'!@#$%^&*()'

from .dbm import connect_db
connect_db(app)

from .bookmodel import BookModel
from .usermodel import UserModel

@app.route("/")
def homepage():
    return render_template("main.html")

@app.route("/register", methods = ["POST"])
def register():
    try:
        if request.form:
            name = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            password = sha256_crypt.hash(password)
            add_user_to_db(name, password, email)
            flash(f"user {name} registered")
            return redirect(url_for("dashboard"))
    except Exception as e:
        return render_template("404.html", exception = e)

@app.route("/login", methods = ["POST"])
def login():
    if request.form:
        username = request.form.get("username")
        password = request.form.get("password")
        print(f"username: {username} password: {password}")
        return render_template("dashboard.html")

@app.route("/dashboard/")
def dashboard():
    try:
        topic_dict = {"Basic": [], "Web Dev": []}
        books = BookModel.query.all()
        gc.collect()
        for book in books:
            topic_dict["Basic"].append([book.name, book.author, book.published])

        return render_template("dashboard.html", topic_dict = topic_dict)
    except Exception as e:
        return render_template("404.html", exception = e)

@app.route("/support/")
def support():
    try:
        flash("We need your support !")
        flash("The world needs your support !")
        return render_template("support.html")
    except Exception as e:
        return render_template("404.html", exception = e)

@app.route("/geturl/", methods = ["POST"])
def get_url():
    if request.form:
        url = request.form.get("url")
        try:
            source = urllib.request.urlopen(url).read()
            soup = bs.BeautifulSoup(source, 'lxml')
            return soup.get_text()
        except Exception as e:
            return f'exception: {str(e)}'
    return render_template("geturl.html")
    
@app.route("/addbook/")
def add_book():
    name = request.args.get("name")
    author = request.args.get("author")
    published = request.args.get("published")
    return add_book_to_db(name, author, published)

@app.route("/getalluser/")
def get_all_user():
    try:
        users = UserModel.query.all()
        gc.collect()
        return jsonify([u.serialize() for u in users])
    except Exception as e:
        return str(e)
        
@app.route("/getallbook/")
def get_all_book():
    try:
        books = BookModel.query.all()
        gc.collect()
        return jsonify([b.serialize() for b in books])
    except Exception as e:
        return str(e)
        
@app.route("/getbook/<id_>/")
def get_by_id(id_):
    try:
        book = BookModel.query.filter_by(id = id_).first()
        gc.collect()
        return jsonify(book.serialize())
    except Exception as e:
        return str(e)
        
@app.route("/addbook/form/", methods = ["POST"])
def add_book_form():
    if request.form:
        name = request.form.get("name")
        author = request.form.get("author")
        published = request.form.get("published")
        return add_book_to_db(name, author, published)
    return render_template("getinput.html")
    
def add_book_to_db(name, author, published):
    try:
        book = BookModel(
            name = name,
            author = author,
            published = published   
        )
        book.db.session.add(book)
        book.db.session.commit()
        gc.collect()
        return f"<h1>Book {name} added, Id {book.id}</h1>"
    except Exception as e:
        return str(e)

def add_user_to_db(name, password, email):
    user = UserModel(
        name = name,
        password = password,
        email = email   
    )
    user.db.session.add(user)
    user.db.session.commit()
    gc.collect()

@app.errorhandler(404)
@app.errorhandler(405)
def page_not_found(e):
    return render_template("404.html", exception = e)

if __name__ == "__main__":
    app.run(debug = True)

print(f"---end of {__name__}---")    