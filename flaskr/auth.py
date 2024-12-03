import functools

from flask import (
    Blueprint, flash, g, request, session, Response
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

""" Register """  
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
			INSERT INTO users (name, username, password)
			VALUES(?, ?, ?)
			""", (name, username, generate_password_hash(password, method='pbkdf2:sha256')))

            # Commit the changes to persist in the database
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
	
	db = get_db()
	error = None

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

	user = db.execute(
		'SELECT * FROM users WHERE username = ?', (username,)
	).fetchone()

	print(user)

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
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return Response(
				'{"error": "Unauthorized"}',
				status=401,
				mimetype='application/json'
			)

        return view(**kwargs)

    return wrapped_view

""" Logout """				
@bp.route('/logout', methods=['POST'])
@login_required
def logout():
	session.clear()
	return Response(
		'You are logged out.',
		status=200,
		mimetype='application/json'
	)

""" Fetch Me """
@bp.route('/me', methods=['GET'])
@login_required
def me():
	user_id = session.get('user_id')

	print(user_id)

	if user_id == None:
		return '{"error": "Unauthorized"}', 401

	db = get_db()
	user = dict(db.execute("""
		SELECT name, username FROM users
		WHERE id = ?
	""", (user_id,)).fetchone())

	print(user)

	return user, 200