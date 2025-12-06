from ..db import db

class Availability(db.Model):
    __tablename__ = "availability"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }