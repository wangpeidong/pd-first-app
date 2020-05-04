print(f"__file__={__file__:<35} | __name__={__name__:<20} | __package__={str(__package__):<20}")

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from os import environ
from flask_wtf import FlaskForm
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from datetime import datetime
import sys

db = None

def connect_db(app):
	#app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://iwwbqrkihpmcuv:bc3d652fa7db25b52de75659f3c321082e35bd99394a8e18d53ff3c54fe524f7@ec2-18-235-97-230.compute-1.amazonaws.com:5432/dbofd7nvd6f68d"
	app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL", "postgresql://postgres:12345@localhost:5432/bookstore")
	app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
	app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
	app.config["JSON_AS_ASCII"] = False
	global db
	db = SQLAlchemy(app)
	return db

def create_all_tables():
    try:
        db.create_all()
        db.session.commit()
    except exc.InvalidRequestError as e:
        db.session.rollback()        
        print(f"Exception: {str(e)}")      
    except exc.SQLAlchemyError as e:
        db.session.rollback()        
        print(f"Exception: {str(e)}")
    except:
        ex_info = sys.exc_info()
        print(f"Error: {ex_info[0]}")

class DBManagementForm(FlaskForm):
    tablename = TextField("Tablename", [validators.Length(min = 3, max = 20), validators.DataRequired()])
    operation = TextField("Operation", [validators.Length(min = 3, max = 20), validators.DataRequired()])
    password = PasswordField("Password", [
        validators.Required(),
        validators.EqualTo("confirm", message = "Passwords must match")
    ])
    confirm = PasswordField("Repeat Password")

    accept_tos = BooleanField(f"I accept the <a href='/about/to'>Terms of Service</a> and <a href='/about/privacy-policy'>Privacy Notice</a> (updated {datetime.now().strftime('%B %d, %Y')})", [validators.Required()])


if __name__ == "__main__":
	pass

print(f"---end of {__name__} ---")    