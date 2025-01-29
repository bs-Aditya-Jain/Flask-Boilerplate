"""This file used to define custom commands.
    ex. python manage.py seed_default_category
"""
from app import app
from app import config_data
from app import db
from app import send_mail_q
from app.helpers.constants import EmailSubject
from app.helpers.constants import EmailTypes
from app.models.user import User
from flask_migrate import Migrate
from flask_migrate import MigrateCommand
from flask_script import Manager
from werkzeug.security import generate_password_hash
from workers import email_worker

migrate = Migrate(app=app, db=db)
# keeps track of all the commands and handles how they are called from the command line
manager = Manager(app)
manager.add_command('db', MigrateCommand)  # type: ignore  # noqa: FKA100


@manager.command
def create_user():
    """This command is used for creating first user(admin)."""
    user_details = User.get_by_email(
        config_data['ADMIN']['PRIMARY_EMAIL'])
    if not user_details:
        # Add user...
        add_user_details = User(first_name=config_data['ADMIN']['NAME'],
                                primary_email=config_data['ADMIN']['PRIMARY_EMAIL'],
                                primary_phone=config_data['ADMIN']['PRIMARY_PHONE'],
                                pin=generate_password_hash(config_data['ADMIN']['PIN'], method='sha256'))
        db.session.add(add_user_details)
        db.session.commit()

        data = {
            'email_to': config_data['ADMIN']['PRIMARY_EMAIL'],
            'subject': EmailSubject.WELCOME_TO_PROJECT.value,
            'template': 'emails/welcome.html',
            'email_type': EmailTypes.INVITE.value,
            'org_id': None,
            'email_data': {
                'email': config_data['ADMIN']['PRIMARY_EMAIL'],
                'pin': config_data['ADMIN']['PIN'],
                'first_name': config_data['ADMIN']['NAME']
            }
        }
        send_mail_q.enqueue(email_worker.EmailWorker.send,  # type: ignore  # noqa: FKA100
                            data, job_timeout=config_data['RQ_JOB_TIMEOUT'])


if __name__ == '__main__':
    manager.run()
