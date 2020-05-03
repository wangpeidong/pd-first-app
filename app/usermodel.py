print(f"__file__={__file__:<35} | __name__={__name__:<20} | __package__={str(__package__):<20}")

from flask import Flask
from .dbm import db, create_all_tables, connect_db

if __name__ == "__main__":  
    db = connect_db(Flask(__name__))

class UserModel(db.Model):
    __tablename__ = "users"
    
    db = db
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(30), unique = True, nullable = False)
    password = db.Column(db.String(100), unique = True, nullable = False)
    email = db.Column(db.String(30), unique = True, nullable = False)
    role = db.Column(db.String(30), unique = False, nullable = True)
    setting = db.Column(db.String(32500), unique = False, nullable = True)
    tracking = db.Column(db.String(32500), unique = False, nullable = True)
    
    def __init__(self, name, password, email, role = "", setting = "", tracking = ""):
        self.name = name
        self.password = password
        self.email = email
        self.role = role
        self.setting = setting
        self.tracking = tracking

    def __repr__(self):
        return f"<Id: {self.id} - Name: {self.name} Email: {self.email}>"
        
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "setting": self.setting,
            "tracking": self.tracking
        }

if __name__ == "__main__":  
    create_all_tables()

print(f"---end of {__name__}---")

# Run from parent folder:
# python -m app.usermodel