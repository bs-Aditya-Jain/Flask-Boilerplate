import traceback

from app import app
from app import config_data
from app import logger
from flask import render_template
from flask_mail import Mail
from flask_mail import Message

app.config['MAIL_SERVER'] = config_data['MAIL']['MAIL_SERVER']
app.config['MAIL_PORT'] = config_data['MAIL']['MAIL_PORT']
app.config['MAIL_USERNAME'] = config_data['MAIL']['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = config_data['MAIL']['MAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = config_data['MAIL']['MAIL_USE_TLS']
app.config['MAIL_USE_SSL'] = config_data['MAIL']['MAIL_USE_SSL']
app.config['MAIL_DEFAULT_SENDER'] = config_data['MAIL']['MAIL_DEFAULT_SENDER']
mail = Mail(app)


def send_mail(email_to, subject, template, email_type, data={}, org_id=None):
    """This method is used to send emails."""
    try:

        msg = Message(subject, sender=(config_data['MAIL']['MAIL_DEFAULT_SENDER_NAME'],
                                       config_data['MAIL']['MAIL_DEFAULT_SENDER']), recipients=[email_to])

        with app.app_context():
            msg.html = render_template(template, data=data)

            response = mail.send(msg)
            logger.info('Mail sent successfully : {0}'.format(response))
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error('Unable to send mail: ' + str(e))
