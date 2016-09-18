from flask import Flask, render_template, request, url_for, redirect, session
from functools import wraps
from sqlalchemy import or_
from markdown import markdown
from database import db, User, Note

app = Flask(__name__)


def login_required(f):
    # Decoration: check login in session
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            session.clear()
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index(data=None):
    return render_template('items/login.html', data=data)


@app.route('/login', methods=['POST'])
def login():
    data = dict()
    if request.form['action'] and request.form['email'] and request.form['password']:
        data['email'] = request.form['email']
        data['password'] = request.form['password']
        if request.form['action'] == 'signup':
            # New user
            # Email check
            my_user = User.query.filter_by(
                email=data['email']).first()
            if not my_user:
                # Create
                my_user = User(data['email'], data['password'])
                db.session.add(my_user)
                db.session.commit()
            else:
                data['error'] = 'register'

        # Checks if the user exists
        if 'error' not in data:
            my_user = User.query.filter_by(
                email=data['email'], password=data['password']).first()
            if my_user:
                # Create user session
                session['user_id'] = my_user.id
                session['user_email'] = my_user.email
                return redirect(url_for('dashboard'))
            else:
                data['error'] = 'login'

    return index(data)


@app.route('/logout')
@login_required
def logout():
    # Clear sessions
    session.clear()

    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard(my_param_note=None):
    my_main_note = None

    # Searchs
    my_notes = my_param_note
    if not my_notes:
        # Nothing found
        my_notes = Note.query.filter_by(
            user_id=session['user_id']).order_by(Note.id.desc()).all()
    if my_notes:
        # Show first result
        my_main_note = my_notes[0]

    # Show first note
    if request.args.get('id'):
        my_note_temp = Note.query.filter_by(id=request.args.get('id')).first()
        # Is there any note in the database?
        if my_note_temp:
            my_main_note = my_note_temp

    # Data for template
    data = dict()
    data['notes'] = my_notes
    data['main_note'] = my_main_note
    data['markdown'] = markdown

    return render_template('items/dashboard.html', data=data)


@app.route('/search')
@login_required
def search():
    q = request.args.get('q')

    return dashboard(Note.query.filter(
        or_(Note.title.like('%' + q + '%'), Note.text.like('%' + q + '%')
            )).filter_by(user_id=session['user_id']).order_by(Note.id.desc()).all())


@app.route('/new')
@login_required
def new():
    return render_template('items/new.html')


@app.route('/new/save', methods=['POST'])
@login_required
def save_note():
    myNote = Note(request.form['title'], request.form[
                  'text'], session['user_id'])
    # Create
    db.session.add(myNote)
    db.session.commit()

    return redirect(url_for('dashboard'))


@app.route('/edit')
@login_required
def edit(data=None):
    id = request.args.get('id')
    my_note = Note.query.filter_by(id=id).first()
    data = dict()
    data['main_note'] = my_note
    return render_template('items/edit.html', data=data)


@app.route('/edit_note', methods=['POST'])
@login_required
def edit_note(data=None):
    if request.form['id']:
        # Update
        my_note = Note.query.filter_by(id=request.form['id']).first()
        my_note.title = request.form['title']
        my_note.text = request.form['text']
        db.session.commit()

    return redirect(url_for('dashboard'))


@app.route('/delete')
@login_required
def delete():
    id = request.args.get('id')
    my_note = Note.query.filter_by(id=id).first()
    data = dict()
    data['main_note'] = my_note
    data['markdown'] = markdown

    return render_template('items/delete.html', data=data)


@app.route('/delete_note')
@login_required
def delete_note():
    id = request.args.get('id')
    # Delete
    my_note = Note.query.filter_by(id=id).first()
    db.session.delete(my_note)
    db.session.commit()

    return redirect(url_for('dashboard', id=id))

# App
if __name__ == "__main__":
    app.secret_key = 'secret'
    app.debug = True
    app.run()
