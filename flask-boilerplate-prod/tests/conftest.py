"""
    This file contains the configuration of settings and initialization of the testing framework for the project.
"""

from app import app_set_configurations
from app import config_data
from app import db
from app import initialize_extensions
from app import ratelimit_handler
from app import register_blueprints
from app import register_swagger_blueprints
from app.models.user import User
from flask import Flask
import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture(scope='session')
def app():
    """
        Initialize the new application instance for the testing with following settings :
            - Default db to test database.
            - Create Schema in the test db as per the models.
            - Yield the application Object.
            - Once test session is ended drop all the tables.
    """

    application = Flask(__name__, instance_relative_config=True)
    application.config.from_object(config_data)

    application.register_error_handler(429, ratelimit_handler)  # type: ignore  # noqa: FKA100
    app_set_configurations(application=application,
                           config_data=config_data)
    application.config.update({
        'TESTING': True,
    })
    application.config.update({
        'SQLALCHEMY_DATABASE_URI': config_data.get('SQLALCHEMY_TEST_DATABASE_URI')
    })

    initialize_extensions(application)
    register_blueprints(application)
    register_swagger_blueprints(application)
    with application.app_context():
        db.create_all()  # creates all the tables

    ctx = application.app_context()
    ctx.push()

    # do the testing
    yield application

    # tear down
    with application.app_context():
        db.session.remove()
        db.drop_all()

    ctx.pop()


@pytest.fixture(scope='session')
def user_client(app):
    """
        This method is being used to fetch the app object to test the admin user test cases.
            - Admin User is created on app object initialization
            - Getting Authenticated
            - Added Auth_token to test_client.
            - At the end of session, User is being deleted from cognito user pool.
    """
    test_user = User(first_name=config_data['ADMIN']['NAME'],
                     primary_email=config_data['ADMIN']['PRIMARY_EMAIL'],
                     primary_phone=config_data['ADMIN']['PRIMARY_PHONE'],
                     pin=generate_password_hash(config_data['ADMIN']['PIN'], method='sha256'))
    db.session.add(test_user)
    db.session.commit()

    yield app.test_client()


def validate_status_code(**kwargs):
    """
        This method is a generic method being used to validate the status_code.
            - Checking if received response status code matches expected status code.
    """

    return kwargs.get('expected') == kwargs.get('received')


def validate_response(**kwargs):
    """
        This method is a generic method being used to validate the response.
            - Checking if received response matches expected.
        1. checks if received and expected are dict
                if they are dict then sort them key wise so that seq of keys in both dict is same
                then iterate over all keys and check if they match
                now recursively call validate response on expected and received value of that key
        2. checks if received and expected are lists and then iterates over the list
                    and if yes then recursively calls validate response on each index  of expected  and received
        3. if received and expected are not dicts neither lists then it directly tries matching them and returns true if macthed
    """
    received = kwargs.get('received')
    expected = kwargs.get('expected')

    if type(received) == dict and type(expected) == dict:
        received_keys = list(kwargs.get('received').keys())
        received_keys.sort()
        sorted_received_dict = {i: kwargs.get(
            'received')[i] for i in received_keys}
        expected_keys = list(kwargs.get('expected').keys())
        expected_keys.sort()
        sorted_expected_dict = {i: kwargs.get(
            'expected')[i] for i in expected_keys}
        for (r_key, r_val), (e_key, e_val) in zip(sorted_received_dict.items(), sorted_expected_dict.items()):
            if r_key == e_key:
                if not validate_response(received=r_val, expected=e_val):
                    return False
            else:
                return False
        return True

    if type(received) == list and type(expected) == list:

        for rec, exp in zip(received, expected):
            if not validate_response(received=rec, expected=exp):
                return False
        return True

    if received == expected or expected == '*':
        return True
