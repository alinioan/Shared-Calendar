import requests
from datetime import datetime
from flask import Blueprint, current_app, jsonify, g, request
from ..utils.decorators import jwt_required, group_role_required
from ..models.group import Group
from ..models.group_user import GroupUser
from ..db import db

groups_bp = Blueprint("groups", __name__)

@groups_bp.post("/")
@jwt_required
def add_group():
    data = request.get_json()
    name = data.get("name")
    description = data.get("description", "")

    keycloak_user = g.user
    group = Group(
        name=name,
        description=description,
        creation_date=datetime.utcnow(),
        last_update=datetime.utcnow()
    )
    db.session.add(group)
    db.session.commit()

    existing = GroupUser.query.filter_by(
        user_id=keycloak_user["keycloak_id"]
    ).first()

    if not existing:
        group_user = GroupUser(
            group_id=group.id,
            email=keycloak_user["email"],
            user_id=keycloak_user["keycloak_id"],
            role="organizer",
            joined_date=datetime.utcnow()
        )

        db.session.add(group_user)
        db.session.commit()

    return jsonify({"message": "Group created successfully",
                    "group": {
                        "id": group.id,
                        "name": group.name,
                        "description": group.description,
                        "creation_date": group.creation_date,
                        "last_update": group.last_update
                    }}), 201

@groups_bp.get("/")
@jwt_required
def get_all_groups():
    groups = Group.query.all()
    return jsonify([group.to_dict() for group in groups]), 200

@groups_bp.get("/<int:group_id>")
@jwt_required
def get_group(group_id):
    group = Group.query.get(group_id)
    
    if not group:
        return jsonify({"error": "Group not found"}), 404
    
    return jsonify(group.to_dict()), 200

@groups_bp.get("/user/")
@jwt_required
def get_user_groups():
    user_id = g.user["keycloak_id"]
    group_users = GroupUser.query.filter_by(user_id=user_id).all()
    group_ids = [gu.group_id for gu in group_users]
    groups = Group.query.filter(Group.id.in_(group_ids)).all()
    return jsonify([group.to_dict() for group in groups]), 200

@groups_bp.delete("/<int:group_id>")
@jwt_required
@group_role_required("organizer")
def delete_group(group_id):
    group = Group.query.get(group_id)
    
    if not group:
        return jsonify({"error": "Group not found"}), 404

    GroupUser.query.filter_by(group_id=group_id).delete(synchronize_session=False)

    db.session.delete(group)
    db.session.commit()
    
    return jsonify({"message": "Group deleted successfully"}), 200

@groups_bp.post("/<int:group_id>/users")
@jwt_required
@group_role_required("organizer")
def add_group_member(group_id):
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "email is required"}), 400

    profile_url = f"{current_app.config['PROFILE_SERVICE_URL']}/profile/user"
    send_data = {"email": email}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {request.headers.get('Authorization').split(' ')[1]}"}
    resp = requests.get(profile_url, json=send_data, headers=headers)

    print("Profile service response:", resp.status_code, resp.text)
    if resp.status_code != 200:
        return jsonify({"error": "User not found in Profile Service"}), 404

    target_user_id = resp.json().get("keycloak_id")
    existing = GroupUser.query.filter_by(
        group_id=group_id,
        user_id=target_user_id
    ).first()

    if existing:
        return jsonify({"error": "User already in group"}), 409

    new_member = GroupUser(
        group_id=group_id,
        email=email,
        user_id=target_user_id,
        role="member",
        joined_date=datetime.now()
    )

    db.session.add(new_member)
    db.session.commit()

    return jsonify({
        "message": "User added to group",
        "group_id": group_id,
        "user_id": target_user_id,
        "role": "member"
    }), 201


@groups_bp.get("/<int:group_id>/users")
@jwt_required
def get_group_members(group_id):
    members = GroupUser.query.filter_by(group_id=group_id).all()
    members_list = [member.to_dict() for member in members]
    return jsonify({"group_id": group_id, "members": members_list}), 200

@groups_bp.delete("/<int:group_id>/users")
@jwt_required
@group_role_required("organizer")
def remove_group_member(group_id):
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "email is required"}), 400

    profile_url = f"{current_app.config['PROFILE_SERVICE_URL']}/profile/user"
    send_data = {"email": email}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {request.headers.get('Authorization').split(' ')[1]}"}
    resp = requests.get(profile_url, json=send_data, headers=headers)

    if resp.status_code != 200:
        return jsonify({"error": "User not found in Profile Service"}), 404

    user = GroupUser.query.filter_by(
        group_id=group_id,
        email=email
    ).first()

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User removed from group"}), 200