from flask import Blueprint, request, jsonify
from models.user import User, db
from uuid import UUID

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
def create_user():
    
    data = request.json
    user = User(username=data['username'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@user_bp.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    # User model uses String(36) for ID, so use string directly
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    # User model uses String(36) for ID, so use string directly
    user = User.query.get_or_404(user_id)
    data = request.json
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    # User model uses String(36) for ID, so use string directly
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204
