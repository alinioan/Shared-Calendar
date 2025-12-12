from flask import Blueprint, jsonify, g
from datetime import datetime
from ..util.decorators import jwt_required
from ..models.user import User
from ..db import db

sync_bp = Blueprint("sync", __name__)

@sync_bp.post("/")
@jwt_required
def sync_profile():
    user_data = g.user
    print(user_data["roles"])
    
    user = User.query.filter_by(keycloak_id=user_data["keycloak_id"]).first()

    if user is None:
        user = User(
            keycloak_id=user_data["keycloak_id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=user_data["roles"][0] if user_data["roles"] else "user",
            creation_date=datetime.utcnow(),
            last_update=datetime.utcnow()
        )
        db.session.add(user)
    else:
        user.email = user_data["email"]
        user.full_name = user_data["full_name"]
        user.role = user_data["roles"][0] if user_data["roles"] else user.role
        user.last_update = datetime.utcnow()

    db.session.commit()

    return jsonify(user.to_dict()), 200
