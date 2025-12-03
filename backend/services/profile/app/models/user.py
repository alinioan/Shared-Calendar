from ..db import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    keycloak_id = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(64), nullable=False)
    creation_date = db.Column(db.DateTime)
    last_update = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "keycloak_id": self.keycloak_id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "creation_date": self.creation_date,
            "last_update": self.last_update
        }
        
