from flask import Flask, render_template, redirect, flash, session, abort
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///login_auth_exercises"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)

toolbar = DebugToolbarExtension(app)

@app.route('/')
def home_page():
    return redirect('/register')

@app.route('/users/<username>')
def user_page(username):
    """A hidden page with user info for logged-in users only"""

    if "username" not in session:
        flash("Please login or register first!", "danger")
        return redirect("/login")
    
    user = User.query.get_or_404(username)
    feedbacks = Feedback.query.filter_by(username=username).all()
    return render_template("user_info.html", user=user, feedbacks=feedbacks)

@app.route('/register', methods=["GET", "POST"])
def register_user():
    """A page to register a user."""
    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = RegisterForm()
    if form.validate_on_submit():
        data = form.data
        del data['csrf_token']
        new_user = User.register(**data)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append("Username taken. Please pick another.")
            return render_template("register.html", form=form)
        
        session['username'] = new_user.username
        session['is_admin'] = new_user.is_admin # keep track of admin status

        # on successful login, redirect to secret page
        return redirect(f'/users/{new_user.username}')
    
    return render_template('register.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login_user():
    """A page for login."""

    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            session['username'] = user.username # keep user logged in
            session['is_admin'] = user.is_admin # keep track of admin status
            return redirect(f'/users/{user.username}')
        else:
            form.username.errors = ['Invalid username/password.']

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    """Log user out and redirect to login page."""

    session.pop("username")
    session.pop('is_admin')
    flash("Goodbye!", "info")
    return redirect("/")

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):
    """A form for users to add more feedback"""

    if "username" not in session:
        flash("Please register or login first!", "danger")
        return redirect('/')
    
    user = User.query.get_or_404(username)

    if user.username != session['username'] and not session['is_admin']:
        # if username doesn't match that in session and not an admin
        flash(f"You don't have permission to add feedbacks under username {username}")
        abort(401, description='Unauthorized access')
    
    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        new_feedback = Feedback(title=title, content=content, username=username)
        db.session.add(new_feedback)
        db.session.commit()
        flash('New feedback added!', 'success')

        return redirect(f"/users/{new_feedback.username}")
    
    return render_template("add_feedback.html", form=form)

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    """This page delete a user and feedbacks related to this user."""

    # Must login or register to access this page
    if "username" not in session:
        flash("Please register or login first!", 'danger')
        return redirect('/')
    
    user = User.query.get_or_404(username)
    if user.username != session['username'] and not session['is_admin']:
        # if username doesn't match that in session
        flash("You don't have permission to do that!", 'danger')
        abort(401, description='Unauthorized access')
    
    db.session.delete(user)
    db.session.commit()

    if not session['is_admin']:
        session.pop('username')
        session.pop('is_admin')
    
    flash(f"User {username} and related feedbacks deleted!", 'info')
    return redirect('/')

@app.route('/feedback/<int:id>/update', methods=['GET', 'POST'])
def update_feedback(id):
    """This page allow user to update a feedback."""

    if "username" not in session:
        flash("Please register or login first!", 'danger')
        return redirect('/')
    
    feedback = Feedback.query.get_or_404(id)

    # if user didn't log in as the owner of this feedback
    if feedback.username != session['username'] and not session['is_admin']:
        flash("You don't have permission to update this feedback!", 'info')
        abort(401, description='Unauthorized access')

    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        data = form.data
        del data['csrf_token']
        for key, value in data.items():
            setattr(feedback, key, value)
        db.session.commit()
        flash('Your feedback has been updated!', 'success')
        return redirect(f"/users/{feedback.username}")
    
    return render_template("update_feedback.html", form=form)

@app.route('/feedback/<int:id>/delete', methods=['POST'])
def delete_feedback(id):
    """Delete a feedback page."""
    if "username" not in session:
        flash("Please register or login first!", 'danger')
        return redirect('/')
    
    feedback = Feedback.query.get_or_404(id)
    feedback_owner = feedback.username

    if session['username'] != feedback_owner and not session['is_admin']:
        flash("You don't have permission to delete this feedback!", 'info')
        abort(401, description='Unauthorized access')
    
    db.session.delete(feedback)
    db.session.commit()
    flash('Feedback deleted!', 'success')
    return redirect(f"/users/{feedback_owner}")

@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 not found page."""
    return render_template('custom_404_not_found_page.html'), 404

@app.errorhandler(401)
def unauthorized(e):
    """Custom 401 page when users are not authenticated or not authorized"""
    return render_template('custom_401_unauthorized_page.html'), 401
