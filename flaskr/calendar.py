import uuid

from flask import (
    Blueprint, session, request, jsonify
)
from flask_cors import cross_origin
from flaskr.db import get_db
from .auth import login_required

bp = Blueprint('calendar', __name__, url_prefix='/calendars')

""" Create a calendar """
@bp.route('', methods=['GET', 'POST'])
@login_required
def calendars():
	# Get user's calendars
	if request.method == 'GET':
		user_id = session.get('user_id')
		db = get_db()

		# Find calendars
		calendars = db.execute("""
			SELECT id, title, access_token
			FROM calendars
			WHERE author_id = ?
		""", (user_id,)).fetchall()

		# Calendars are now dictionaries thanks to the row_factory
		calendars_list = [dict(row) for row in calendars]

		return calendars_list
	
	# Create a new calendar
	else:
		user_id = session.get('user_id')
		print(user_id)

		data = request.get_json()
		title = data.get('title')
		notes = data.get('notes')

		if not title:
			return 'Title is requred.', 400
		
		if not notes or len(notes) != 24:
			return 'There should be 24 notes.', 400

		db = get_db()

		# Generate a unique ID
		unique_id = str(uuid.uuid4())

		# Insert a new calendar into db
		db.execute("""
			INSERT INTO calendars (author_id, title, access_token)
			VALUES (?, ?, ?)
		""", (user_id, title, unique_id,))

		# Commit the changes to persist in the database
		db.commit()

		# Retrieve the created calendar
		calendar = db.execute("SELECT id, title, access_token FROM calendars WHERE access_token = ?", (unique_id,)).fetchone()

		# Insert 24 notes into db
		for note in notes:
			db.execute("""
				INSERT INTO notes (author_id, calendar_id, description, day)
				VALUES (?, ?, ?, ?)
			""", (user_id, calendar['id'], note['description'], note['day'],))
			
			# Commit the changes to persist in the database
			db.commit()
		
		# Find notes related to the calendar
		notes = db.execute("""
			SELECT
				day,
				description,
				opened_at
			FROM notes
			WHERE calendar_id = ?
		""", (calendar['id'],))

		notes_dict = [dict(note) for note in notes]

		# Convert Row object to dictionary
		calendar_dict = dict(calendar)

		# Add notes to the calendar dictionary
		calendar_dict['notes'] = notes_dict

		return jsonify(calendar_dict), 201
	
	

""" Get calendar data """
@bp.route('/<token>', methods=['GET'])
def calendar(token):
	db = get_db()
	error = None
	
	# Find the calendar
	calendar = db.execute("""
		SELECT
			id,
			title,
			access_token					
		FROM calendars
		WHERE access_token = ?
	""", (token,)).fetchone()

	# Check if the calendar was found
	if not calendar:
		return "Not found"
	
	# Find notes related to the calendar
	notes = db.execute("""
		SELECT
			day,
			description,
			opened_at
		FROM notes
		WHERE calendar_id = ?
	""", (calendar['id'],))

	notes_dict = [dict(note) for note in notes]

	# Convert Row object to dictionary
	calendar_dict = dict(calendar)

	# Add notes to the calendar dictionary
	calendar_dict['notes'] = notes_dict

	return jsonify(calendar_dict), 200
	

""" Update opened day """
@bp.route('/<token>/notes/<day>', methods=['POST'])
def notes(token, day):
	db = get_db()

	# Retrieve the current calendar
	calendar_dict = dict(db.execute("SELECT * FROM calendars WHERE access_token = ?", (token,)).fetchone())
	
	# Ensure that calendar was found
	if not calendar_dict:
		return jsonify('Calendar not found'), 400
	
	# Retrieve the current note
	note = dict(db.execute("""
		SELECT
			day,
			description,
			opened_at
		FROM notes
		WHERE calendar_id = ?
		AND day = ?
	""", (calendar_dict['id'], int(day),)).fetchone())

	# Ensure that note was not opened yet
	if note['opened_at']:
		return note, 200

	# Update the current note as opened
	db.execute("""
		UPDATE notes
		SET opened_at = CURRENT_TIMESTAMP
		WHERE calendar_id = ?
		AND day = ?
	""", (calendar_dict['id'], int(day),))

	# Commit the changes to persist in the database
	db.commit()
	
	# Retrieve the updated note
	note = dict(db.execute("""
		SELECT
			day,
			description,
			opened_at
		FROM notes
		WHERE calendar_id = ?
		AND day = ?
	""", (calendar_dict['id'], int(day),)).fetchone())

	return note, 200