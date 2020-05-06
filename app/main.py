print(f"__file__={__file__:<35} | __name__={__name__:<20} | __package__={str(__package__):<20}")

from flask import Flask, request, jsonify, render_template, flash, redirect, url_for, session, Markup, send_file
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt
from functools import wraps
import bs4 as bs
import urllib.request
import gc, os, json
import pygal
import plotly
import plotly.graph_objs as go
import pandas_datareader.data as web
import datetime

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

def get_files_list():
    files = []
    # r=root, d=directories, f=files
    for r, d, f in os.walk(app.root_path):
        for file in f:
            # strip app.root_path 
            files.append(os.path.join(r, file).split(app.root_path, 1)[1])
    return files

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
#@app.route("/<path:anypath>/")
@app.route("/")
def homepage():
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

@app.route('/_background_process/')
def background_process():
    try:
        lang = request.args.get('proglang', 0, type = str)
        if lang.lower() == 'python':
            return jsonify(result = 'You are wise')
        else:
            return jsonify(result = 'Try again.')
    except Exception as e:
        return str(e)

@app.route('/jQuery-example/')
def interactive():
    return render_template('jQuery-example.html')

@app.route("/upload-file/", methods = ["GET", "POST"])
@privilege_login_required(None)
def upload_file():
    try:
        result = None
        if request.method == "POST":
          f = request.files["file"]
          f.save(secure_filename(f.filenagitme))
          result = f"The file {f.filename} uploaded successfully"
        return render_template("upload-file.html",  result = result)
    except Exception as e:
        return render_template("404.html", exception = e)

@app.route("/send-mail/", methods = ["GET", "POST"])
@privilege_login_required(None)
def send_mail():
    try:
        result = None
        if request.form and request.method == "POST":
            server = request.form.get("server")
            username = request.form.get("username")
            password = request.form.get("password")
            from_ = request.form.get("from")
            to_list = request.form.get("to").split(";")
            title = request.form.get("title")
            body = request.form.get("body")

            app.config.update(
                DEBUG=True,
                #EMAIL SETTINGS
                MAIL_SERVER = server,
                MAIL_PORT = 465,
                MAIL_USE_SSL = True,
                MAIL_USERNAME = username,
                MAIL_PASSWORD = password
            )
            mail = Mail(app)
            msg = Message(title, sender = from_, recipients = to_list)
            msg.body = body
            mail.send(msg)
            result = "The email sent successfully."
        return render_template("send-mail.html",  result = result)
    except Exception as e:
        return render_template("404.html", exception = e)

@app.route("/graph-example/")
def graph_example():
    try:
        start = datetime.datetime(2020, 1, 1)
        end = datetime.datetime.now()
        df = web.DataReader("^GSPC", "yahoo", start, end)
        df.reset_index(inplace = True)
        df.set_index("Date", inplace = True)

        graph = pygal.Line()
        graph.title = "Pygal Graph (^GSPC)"
        graph.x_labels = df.index.tolist()
        graph.add("Open", df["Open"].tolist())
        graph.add("High", df["High"].tolist())
        graph.add("Low", df["Low"].tolist())
        graph.add("Close", df["Adj Close"].tolist())
        graph_data = graph.render_data_uri()

        layout = go.Layout(title_text = "Plotly Graph (^GSPC)", title_x = 0.5)
        trace1 = go.Scatter(x = df.index, y = df["Open"], name = "Open")
        trace2 = go.Scatter(x = df.index, y = df["High"], name = "High")
        trace3 = go.Scatter(x = df.index, y = df["Low"], name = "Low")
        trace4 = go.Scatter(x = df.index, y = df["Adj Close"], name = "Close")
        data = [trace1, trace2, trace3, trace4]
        fig = go.Figure(data = data, layout = layout)
        fig_data = json.dumps(fig, cls = plotly.utils.PlotlyJSONEncoder)

        return render_template("graphing.html", graph_data = graph_data, fig_data = fig_data)
    except Exception as e:
        return(str(e))

@app.route("/dashboard/")
@privilege_login_required(None)
def dashboard():
    try:
        topic_dict = {"Book": [], "User": [], "File": []}
        books = BookModel.query.all()
        users = UserModel.query.all()
        gc.collect()
        for book in books:
            topic_dict["Book"].append([book.name, book.author, book.published])
        for user in users:
            topic_dict["User"].append([user.name, user.email, user.password, user.role, user.setting, user.tracking])
        topic_dict["File"] = get_files_list()

        return render_template("dashboard.html", topic_dict = topic_dict)
    except Exception as e:
        return render_template("404.html", exception = e)

@app.route("/getfile/<path:file>/")
@privilege_login_required("Admin")
def getfile(file):
    try:
        # The attachment_filename was not working when retrieveing from under os.getcwd()
        # but worked when retrieveing from under app.root_path
        filename = file.split("/")[-1]
        return send_file(file, as_attachment = True, attachment_filename = filename)
    except Exception as e:
        return str(e)

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

@app.route("/getbook/")        
@app.route("/getbook/<int:id_>/")
def get_by_id(id_ = 1):
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