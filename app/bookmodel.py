print(f"__file__={__file__:<35} | __name__={__name__:<20} | __package__={str(__package__):<20}")

from .main import db

class BookModel(db.Model):
    __tablename__ = "books"
    
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

from sqlalchemy import exc
if __name__ == "__main__":  
    try:
        db.create_all()
        db.session.commit()
    except exc.InvalidRequestError as e:
        db.session.rollback()        
        print(f"Exception: {str(e)}")      
    except exc.SQLAlchemyError as e:
        db.session.rollback()        
        print(f"Exception: {str(e)}")

#run from parent folder
#python -m app.bookmodel
print("---end of bookmodel---")