import jwt
from flask import request, g, jsonify, current_app
from functools import wraps

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

        g.user = {
            "keycloak_id": payload.get("sub"),
            "email": payload.get("email"),
            "full_name": payload.get("name"),
            "roles": payload.get("realm_access", {}).get("roles", [])
        }

        return f(*args, **kwargs)
    return decorated
