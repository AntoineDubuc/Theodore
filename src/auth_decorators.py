"""
Authentication Decorators for Theodore
Provides decorators for route protection and user management
"""

from functools import wraps
from flask import jsonify, request, redirect, url_for, flash
from flask_login import current_user

def optional_auth(f):
    """
    Decorator that allows access but provides user context if authenticated
    Useful for features that work better with authentication but don't require it
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Always allow access, just pass current_user context
        return f(*args, **kwargs)
    return decorated_function

def require_auth(f):
    """
    Decorator that requires authentication for access
    Redirects to login page for web requests, returns 401 for API requests
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please log in to access this resource'
                }), 401
            else:
                flash('Please log in to access this page.', 'info')
                return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorator that requires admin privileges
    For future use when admin features are implemented
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            else:
                flash('Please log in to access this page.', 'info')
                return redirect(url_for('auth.login', next=request.url))
        
        # For now, all authenticated users are considered admins
        # In the future, add actual admin role checking here
        # if not current_user.is_admin:
        #     if request.is_json or request.path.startswith('/api/'):
        #         return jsonify({'error': 'Admin privileges required'}), 403
        #     else:
        #         flash('You do not have permission to access this page.', 'error')
        #         return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def api_auth_optional(f):
    """
    Decorator for API endpoints that benefit from authentication but don't require it
    Adds user context to the response if authenticated
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Call the function and get the response
        response = f(*args, **kwargs)
        
        # If it's a JSON response and user is authenticated, add user context
        if (hasattr(response, 'get_json') and 
            current_user.is_authenticated and 
            response.status_code == 200):
            
            data = response.get_json()
            if isinstance(data, dict):
                data['user_context'] = {
                    'authenticated': True,
                    'username': current_user.username,
                    'email': current_user.email
                }
                # Update the response
                response.data = jsonify(data).data
        
        return response
    return decorated_function