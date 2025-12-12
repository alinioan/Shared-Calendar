import jwt
import requests
from flask import request, g, jsonify, current_app
from functools import wraps

from ..models.group_user import GroupUser

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ")[1]

        jwks_url = f"{current_app.config['KEYCLOAK_URL']}/realms/{current_app.config['KEYCLOAK_REALM']}/protocol/openid-connect/certs"
        
        try:
            jwks_client = jwt.PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False}
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 401

        print("Decoded JWT payload:", payload)
        g.user = {
            "keycloak_id": payload.get("sub"),
            "email": payload.get("email"),
            "full_name": payload.get("name"),
            "roles": payload.get("realm_access", {}).get("roles", [])
        }

        try:
            sync_url = f"{current_app.config['PROFILE_SERVICE_URL']}/sync"
            sync_headers = {"Authorization": f"Bearer {token}"}
            sync_resp = requests.post(sync_url, headers=sync_headers)

            if sync_resp.status_code not in (200, 201):
                return jsonify({
                    "error": "Failed to sync user profile",
                    "details": sync_resp.text
                }), 503

        except Exception:
            return jsonify({"error": "Profile Service unavailable"}), 503

        return f(*args, **kwargs)
    return decorated

def group_role_required(required_role):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            group_id = kwargs.get("group_id")

            if not group_id:
                return jsonify({"error": "group_id missing from route"}), 400

            user_id = g.user["keycloak_id"]

            membership = GroupUser.query.filter_by(
                group_id=group_id,
                user_id=user_id
            ).first()

            if not membership:
                return jsonify({"error": "User is not a member of this group"}), 403

            if membership.role != required_role:
                return jsonify({
                    "error": f"User must have role '{required_role}' for this action"
                }), 403

            return f(*args, **kwargs)
        return decorated
    return wrapper

