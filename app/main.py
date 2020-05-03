print(f"__file__={__file__:<35} | __name__={__name__:<20} | __package__={str(__package__):<20}")

from flask import Flask, request, jsonify, render_template

import bs4 as bs
import urllib.request

app = Flask(__name__)

@app.route("/")
def homepage():
    return render_template("main.html")

@app.route("/login", methods = ["POST"])
def handle_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        print(f"username: {username} password: {password}")
        return render_template("dashboard.html")

@app.route("/dashboard/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/support/")
def support():
    return render_template("support.html")

@app.route("/geturl/", methods = ["GET", "POST"])
def get_url():
    if request.method == "POST":
        url = request.form.get("url")
        try:
            source = urllib.request.urlopen(url).read()
            soup = bs.BeautifulSoup(source, 'lxml')
            return soup.get_text()
        except Exception as e:
            return f'exception: {str(e)}'
    return render_template("geturl.html")
    
from app.bookmodel import BookModel

@app.route("/addbook/")
def add_book():
    name = request.args.get("name")
    author = request.args.get("author")
    published = request.args.get("published")
    return add_book_to_db(name, author, published)
        
@app.route("/getallbook/")
def get_all_book():
    try:
        books = BookModel.query.all()
        return jsonify([b.serialize() for b in books])
    except Exception as e:
        return str(e)
        
@app.route("/getbook/<id_>/")
def get_by_id(id_):
    try:
        book = BookModel.query.filter_by(id = id_).first()
        return jsonify(book.serialize())
    except Exception as e:
        return str(e)
        
@app.route("/addbook/form/", methods = ["GET", "POST"])
def add_book_form():
    if request.method == "POST":
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
        return f"<h1>Book {name} added, Id {book.id}</h1>"
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    app.run(debug = True)

print(f"---end of {__name__}---")    