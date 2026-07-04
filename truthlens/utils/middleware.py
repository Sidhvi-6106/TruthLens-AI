from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from truthlens.models.user import User


def require_role(*roles):
    """
    Decorator to protect routes requiring specific roles.
    Assumes JWT token is validated first.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception as e:
                return jsonify({"error": "Missing or invalid authorization token."}), 401
            
            email = get_jwt_identity()
            user = User.query.filter_by(email=email).first()
            if not user:
                return jsonify({"error": "Authenticated user not found."}), 401
            
            if user.is_locked():
                return jsonify({"error": "Account is temporarily locked due to security policy."}), 403
                
            user_role = user.role.name if user.role else "User"
            if user_role not in roles:
                return jsonify({"error": f"Unauthorized. This endpoint requires role permission in: {roles}."}), 403
                
            return fn(*args, **kwargs)
        return wrapper
    return decorator
