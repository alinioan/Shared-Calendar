from flask import Blueprint, jsonify, g
from ..util.decorators import jwt_required
from ..models.user import User

profile_bp = Blueprint("profile", __name__)

@profile_bp.get("/")
@jwt_required
def get_profile():
    user = User.query.filter_by(keycloak_id=g.user["keycloak_id"]).first()

    if not user:
        return jsonify({"error": "Profile not found. Run /sync first."}), 404

    return jsonify(user.to_dict()), 200
