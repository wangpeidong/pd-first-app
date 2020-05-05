print(f"__file__={__file__:<35} | __name__={__name__:<20} | __package__={str(__package__):<20}")

from flask import Flask, request, jsonify, render_template, flash, redirect, url_for, session, Markup
from passlib.hash import sha256_crypt
from functools import wraps
import bs4 as bs
import urllib.request
import gc

app = Flask(__name__)
app.secret_key = b'!@#$%^&*()'

from .dbm import connect_db, DBManagementForm
connect_db(app)

from .bookmodel import BookModel
from .usermodel import UserModel

# Define decorator/wrapper
def privilege_login_required(privilege):
    def login_required(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            if privilege:
                if "username" in session and privilege == session["username"]:
                    return f(*args, **kwargs)
                else:
                    flash("You must login with privilege first !")
                    return redirect(url_for("homepage"))
            else:
                if "logged_in" in session:
                    return f(*args, **kwargs)
                else:
                    flash("You must login first !")
                    return redirect(url_for("homepage"))
        return wrap
    return login_required

def add_book_to_db(name, author, published):
    try:
        book = BookModel(
            name = name,
            author = author,
            published = published   
        )
        book.add_to_db()
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
    user.add_to_db()
    gc.collect()

tables = {'book': BookModel, 'user': UserModel}    
def exec_table_operation(table, operation):
    try:
        if operation == "selectall":
            results = tables[table].query.all()
            return jsonify([r.serialize() for r in results]).get_data(as_text = True)
        elif operation.startswith("delete"):
            idx = int(operation.split()[1])
            item = tables[table].query.get(idx)
            js = item.serialize()
            item.delete_from_db()
            return jsonify(js).get_data(as_text = True) + "\n deleted"

        gc.collect()
    except Exception as e:
        return str(e)

# Use dynamic url to return anypath not being routed to homepage
@app.route("/<path:anypath>/")
@app.route("/")
def homepage(anypath = "/"):
    return render_template("main.html",  message=Markup("<h1>Welcome to PD homepage !</h1>"))

@app.route("/managedb", methods = ["GET", "POST"])
@privilege_login_required("Admin")
def managedb():
    try:
        # No need to pass request.form to Flask-WTF, it will load automatically
        # and the validate_on_submit will check if it is a valid POST.
        form = DBManagementForm()

        if form.validate_on_submit():
            result = exec_table_operation(form.tablename.data, form.operation.data)
            return render_template("managedb.html", form = form, result = result)
        if form.errors:
            print(f"error in managedb: {form.errors}")
        return render_template("managedb.html", form = form, result = None)
    except Exception as e:
        return render_template("404.html", exception = e)

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

            session["logged_in"] = True
            session["username"] = name
            return render_template("main.html",  message=Markup(f"<h1>user {name} registered !</h1>"))
    except Exception as e:
        return render_template("404.html", exception = e)

@app.route("/login", methods = ["POST"])
def login():
    try:
        if request.form:
            name = request.form.get("username")
            password = request.form.get("password")
            print(f"username: {name} password: {password}")

            user = UserModel.query.filter_by(name = name).first()
            if (user and sha256_crypt.verify(password, user.password)):
                flash(f"Welcome")
                session["logged_in"] = True
                session["username"] = name
                return render_template("main.html",  message=Markup(f"<h1>user {name} logged in !</h1>"))
            flash(f"Alert")
            return render_template("main.html",  message=Markup(f"<h1>user {name} credential not correct !</h1>"))
    except Exception as e:
        return render_template("404.html", exception = e)

@app.route("/logout", methods = ["GET", "POST"])
@privilege_login_required(None)
def logout():
    try:
        if request.method == "GET":
            return redirect(url_for("homepage") + "#logoutModal")
        name = session["username"]
        flash(f"You are logged out.")
        session.clear()
        return render_template("main.html",  message=Markup(f"<h1>user {name} logged out !</h1>"))
    except Exception as e:
        return render_template("404.html", exception = e)

@app.route("/dashboard/")
@privilege_login_required(None)
def dashboard():
    try:
        topic_dict = {"Book": [], "User": []}
        books = BookModel.query.all()
        users = UserModel.query.all()
        gc.collect()
        for book in books:
            topic_dict["Book"].append([book.name, book.author, book.published])
        for user in users:
            topic_dict["User"].append([user.name, user.email, user.password, user.role, user.setting, user.tracking])

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

@app.route("/search", methods = ["GET", "POST"])
def search():
    try:
        if request.form and request.method == "POST":
            url = ("http://www.google.com/search?q=" + urllib.parse.quote(request.form.get("search"))) #in case search string is unicode, covert it to ascii
            print(url)
            # space is not valid character in URL, needs to be coverted to %20,
            # for example https://www.google.com/search?q=python%20w3school
            url = urllib.request.Request(url.replace(" ", "%20"), headers = {"User-Agent": "Mozilla/5.0"})
            source = urllib.request.urlopen(url).read()
            soup = bs.BeautifulSoup(source, 'lxml')
            return render_template("main.html", message = Markup(soup.get_text()))
    except Exception as e:
        return render_template("404.html", exception = e)

@app.route("/geturl/", methods = ["GET", "POST"])
def get_url():
    try:
        if request.form and request.method == "POST":
            url = request.form.get("url")
            # pretend the requst is from browser to avoid bot detection
            url = urllib.request.Request(url, headers = {"User-Agent": "Mozilla/5.0"})
            source = urllib.request.urlopen(url).read()
            soup = bs.BeautifulSoup(source, 'lxml')
            return render_template("geturl.html", result = Markup(soup.get_text()))
        return render_template("geturl.html")
    except Exception as e:
        return render_template("404.html", exception = e)
    
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
        
@app.route("/getbook/<int:id_>/")
def get_by_id(id_):
    try:
        book = BookModel.query.filter_by(id = id_).first()
        gc.collect()
        return jsonify(book.serialize())
    except Exception as e:
        return str(e)
        
@app.route("/addbook/form/", methods = ["GET", "POST"])
def add_book_form():
    if request.form:
        name = request.form.get("name")
        author = request.form.get("author")
        published = request.form.get("published")
        return render_template("getinput.html", result = add_book_to_db(name, author, published))
    return render_template("getinput.html")
    
@app.errorhandler(404)
@app.errorhandler(405)
def page_not_found(e):
    flash("You've got an error !")
    return render_template("404.html", exception = e)

if __name__ == "__main__":
    app.run(debug = True)

print(f"---end of {__name__}---")    