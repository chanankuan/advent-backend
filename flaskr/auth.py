import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Response
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

""" Login """  
@bp.route('/register', methods=['POST'])
def register():
	data = request.get_json()
	name = data.get('name')
	username = data.get('username')
	password = data.get('password')

	# Define expected fields
	expected_fields = ['name', 'username', 'password']    

	# Find any extra fields in the request
	extra_fields = [key for key in data.keys() if key not in expected_fields]

    # If there are extra fields, return an error
	if extra_fields:
		return Response(
            f'{{"error": "Extra fields received: {", ".join(extra_fields)}"}}',
            status=400,
            mimetype='application/json'
        )

	db = get_db()
	error = None

	if not name:
		error = 'Name is required.'
	elif not username:
		error = 'Username is required.'
	elif not password:
		error = 'Password is required.'

	if error is None:
		try:
			db.execute("""
			INSERT INTO user (name, username, password)
			VALUES(?, ?, ?)
			""", (name, username, generate_password_hash(password, method='pbkdf2:sha256')))

			db.commit()
		except db.IntegrityError:
			error = f"User {username} is already registered."
		else:
			return Response(
				f'{{"name": "{name}", "username": "{username}"}}',
				status=201,
				mimetype='application/json'
			)
		
	flash(error)
	return Response(
		f'{{"error": "{error}"}}',
		status=400,
		mimetype='application/json'
	)


""" Login """   
@bp.route('/login', methods=['POST'])
def login():
	data = request.get_json()
	username = data.get('username')
	password = data.get('password')

	if not username:
		error = 'Username is required.'
	elif not password:
		error = 'Password is required.'

	# Define expected fields
	expected_fields = ['username', 'password']    

	# Find any extra fields in the request
	extra_fields = [key for key in data.keys() if key not in expected_fields]

    # If there are extra fields, return an error
	if extra_fields:
		return Response(
            f'{{"error": "Extra fields received: {", ".join(extra_fields)}"}}',
            status=400,
            mimetype='application/json'
        )

	db = get_db()
	error = None

	user = db.execute(
		'SELECT * FROM user WHERE username = ?', (username,)
	).fetchone()

	if user is None:
		error = 'Incorrect username or password.'
	elif not check_password_hash(user['password'], password):
		error = 'Incorrect username or password.'

	if error is None:
		session.clear()
		session['user_id'] = user['id']

		return Response(
			f'{{"name": "{user["name"]}", "username": "{username}"}}',
			status=200,
			mimetype='application/json'
		)
	
	flash(error)
	return Response(
		f'{{"error": "{error}"}}',
		status=400,
		mimetype='application/json'
	)

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

""" Logout """				
@bp.route('/logout')
def logout():
	session.clear()
	return Response(
		'You are logged out.',
		status=200,
		mimetype='application/json'
	)

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view