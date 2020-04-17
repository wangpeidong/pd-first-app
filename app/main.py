print(f"__file__={__file__:<35} | __name__={__name__:<20} | __package__={str(__package__):<20}")

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from os import environ

app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://iwwbqrkihpmcuv:bc3d652fa7db25b52de75659f3c321082e35bd99394a8e18d53ff3c54fe524f7@ec2-18-235-97-230.compute-1.amazonaws.com:5432/dbofd7nvd6f68d"
app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL", "postgresql://postgres:12345@localhost:5432/bookstore")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
app.config["JSON_AS_ASCII"] = False

db = SQLAlchemy(app)

@app.route("/")
def home_view():
    return "<h1>Welcome to PD-First-App</h1>"
    
@app.route("/name/<name>")
def get_book_name(name):
    return f"<h1>Name: {name}</h1>"
    
@app.route("/details")
def get_book_details(): 
    author = request.args.get("author")
    published = request.args.get("published")
    return f"<h1>Author: {author}, Published: {published}</h1>"
    
from app.bookmodel import BookModel

@app.route("/add")
def add_book():
    name = request.args.get("name")
    author = request.args.get("author")
    published = request.args.get("published")
    try:
        book = BookModel(
            name = name,
            author = author,
            published = published
        )
        db.session.add(book)
        db.session.commit()
        return f"<h1>Book {name} added, Id {book.id}</h1>"
    except Exception as e:
        return str(e)
        
@app.route("/getall")
def get_all():
    try:
        books = BookModel.query.all()
        return jsonify([e.serialize() for e in books])
    except Exception as e:
        return str(e)
        
@app.route("/get/<id_>")
def get_by_id(id_):
    try:
        book = BookModel.query.filter_by(id = id_).first()
        return jsonify(book.serialize())
    except Exception as e:
        return str(e)
        
@app.route("/add/form", methods = ["GET", "POST"])
def add_book_form():
    if request.method == "POST":
        name = request.form.get("name")
        author = request.form.get("author")
        published = request.form.get("published")
        try:
            book = BookModel(
                name = name,
                author = author,
                published = published   
            )
            db.session.add(book)
            db.session.commit()
            return f"<h1>Book {name} added, Id {book.id}</h1>"
        except Exception as e:
            return str(e)
    return render_template("getinput.html")
    
print("---end of main---")    