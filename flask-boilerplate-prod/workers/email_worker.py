"""Contains methods and logic to send emails."""
import traceback

from app import logger
from providers.mail import send_mail


class EmailWorker:
    """This worker contains different methods for sending email."""
    @classmethod
    def send(cls, data):
        """This method is used for sending emails."""
        try:
            email_to = data.get('email_to', None)  # type: ignore  # noqa: FKA100
            subject = data.get('subject', None)  # type: ignore  # noqa: FKA100
            template = data.get('template', None)  # type: ignore  # noqa: FKA100
            email_type = data.get('email_type', None)  # type: ignore  # noqa: FKA100
            email_data = data.get('email_data', None)  # type: ignore  # noqa: FKA100
            org_id = data.get('org_id', None)  # type: ignore  # noqa: FKA100
            logger.info('sent mail')
            send_mail(email_to=email_to, subject=subject, template=template,
                      email_type=email_type, data=email_data, org_id=org_id)
        except Exception as e:
            logger.error(
                'Inside EmailWorker.send() : ' + str(e))
            logger.error(traceback.format_exc())
