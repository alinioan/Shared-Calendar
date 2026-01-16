import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base

base = declarative_base()

class Group(base):
    __tablename__ = "group"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(1024))
    creation_date = db.Column(db.DateTime)
    last_update = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "creation_date": self.creation_date,
            "last_update": self.last_update,
        }
