from ..db import db

class Event(db.Model):
    __tablename__ = "event"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(1024))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("group_user.id"), nullable=False)
    creation_date = db.Column(db.DateTime)
    last_update = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "created_by": self.created_by,
            "creation_date": self.creation_date,
            "last_update": self.last_update,
        }