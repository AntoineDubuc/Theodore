"""
Authentication Routes for Theodore
Handles login, registration, and logout endpoints
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from pydantic import ValidationError
from auth_models import UserAlreadyExistsError, InvalidCredentialsError, AuthError

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page and handler"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    # Handle POST request
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        if not email or not password:
            error_msg = 'Email and password are required'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/login.html')
        
        # Get auth manager from Flask current app
        from flask import current_app
        auth_manager = current_app.auth_manager
        
        # Authenticate user
        user = auth_manager.authenticate_user(email, password, remember_me)
        
        # Log user in
        login_user(user, remember=remember_me)
        
        # Success response
        success_msg = f'Welcome back, {user.username}!'
        if request.is_json:
            return jsonify({
                'success': True, 
                'message': success_msg,
                'user': {
                    'email': user.email,
                    'username': user.username
                }
            })
        
        flash(success_msg, 'success')
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('index'))
        
    except InvalidCredentialsError:
        error_msg = 'Invalid email or password'
        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 401
        flash(error_msg, 'error')
        return render_template('auth/login.html')
        
    except Exception as e:
        error_msg = f'Login failed: {str(e)}'
        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 500
        flash(error_msg, 'error')
        return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page and handler"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    # Handle POST request
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not all([email, username, password, confirm_password]):
            error_msg = 'All fields are required'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/register.html')
        
        # Get auth manager from Flask current app
        from flask import current_app
        auth_manager = current_app.auth_manager
        
        # Register user
        user = auth_manager.register_user(email, username, password, confirm_password)
        
        # Log user in immediately after registration
        login_user(user)
        
        # Success response
        success_msg = f'Welcome to Theodore, {user.username}!'
        if request.is_json:
            return jsonify({
                'success': True, 
                'message': success_msg,
                'user': {
                    'email': user.email,
                    'username': user.username
                }
            })
        
        flash(success_msg, 'success')
        return redirect(url_for('index'))
        
    except UserAlreadyExistsError as e:
        error_msg = str(e.message)
        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 409
        flash(error_msg, 'error')
        return render_template('auth/register.html')
        
    except ValidationError as e:
        # Extract validation errors
        errors = []
        for error in e.errors():
            field = error['loc'][-1] if error['loc'] else 'field'
            message = error['msg']
            errors.append(f"{field.replace('_', ' ').title()}: {message}")
        
        error_msg = '; '.join(errors)
        if request.is_json:
            return jsonify({'success': False, 'error': error_msg, 'validation_errors': errors}), 400
        flash(error_msg, 'error')
        return render_template('auth/register.html')
        
    except Exception as e:
        error_msg = f'Registration failed: {str(e)}'
        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 500
        flash(error_msg, 'error')
        return render_template('auth/register.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """User logout"""
    username = current_user.username if current_user.is_authenticated else 'User'
    logout_user()
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/api/me')
@login_required
def current_user_info():
    """Get current user information via API"""
    return jsonify({
        'authenticated': True,
        'user': {
            'email': current_user.email,
            'username': current_user.username
        }
    })

@auth_bp.route('/api/check')
def check_auth():
    """Check authentication status"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': {
                'email': current_user.email,
                'username': current_user.username
            }
        })
    else:
        return jsonify({'authenticated': False})

# Error handlers for auth blueprint
@auth_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized access"""
    if request.is_json:
        return jsonify({'error': 'Authentication required'}), 401
    flash('Please log in to access this page.', 'info')
    return redirect(url_for('auth.login', next=request.url))

@auth_bp.errorhandler(403)
def forbidden(error):
    """Handle forbidden access"""
    if request.is_json:
        return jsonify({'error': 'Access forbidden'}), 403
    flash('You do not have permission to access this page.', 'error')
    return redirect(url_for('index'))