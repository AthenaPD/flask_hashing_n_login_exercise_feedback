"""Seed file to make sample users for database."""

from models import User, Feedback, db
from app import app


with app.app_context():
    # Create all tables
    db.drop_all()
    db.create_all()

    # Empty table if it's not
    User.query.delete()
    Feedback.query.delete()

    # # Add some users
    # dad = User(username='Daddy', password='OrionsDad', email="rujdeka@gmail.com", first_name="Ruj", last_name='Deka')
    # mom = User(username='Mommy', password='OrionsMom', email="apan@gmail.com", first_name="Thena", last_name='Poon')

    # db.session.add_all([dad, mom])
    # db.session.commit()
