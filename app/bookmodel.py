print(f"__file__={__file__:<35} | __name__={__name__:<20} | __package__={str(__package__):<20}")

from .dbm import db, create_all_tables

class BookModel(db.Model):
    __tablename__ = "books"
    
    db = db
    
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String())
    author = db.Column(db.String())
    published = db.Column(db.String())
    
    def __init__(self, name, author, published):
        self.name = name
        self.author = author
        self.published = published
        
    def __repr__(self):
        return f"<Id {self.id} - Book {self.name}>"
        
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "author": self.author,
            "published": self.published
        }

if __name__ == "__main__":  
    create_all_tables()

#run from parent folder
#python -m app.bookmodel
print(f"---end of {__name__}---")