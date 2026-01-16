import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base

from models.base import Base

class Job(Base):
    __tablename__ = "job"

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(25), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status
        }
