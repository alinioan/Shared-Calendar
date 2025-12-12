from ..db import db

class GroupUser(db.Model):
    __tablename__ = "group_user"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.String(50), nullable=False, unique=True)
    role = db.Column(db.String(50), nullable=False)
    joined_date = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "user_id": self.user_id,
            "role": self.role,
            "joined_date": self.joined_date,
        }