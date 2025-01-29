"""This file initializes Application."""
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import subprocess
import sys
import traceback

from app.helpers.constants import HttpStatusCode
from app.helpers.constants import QueueName
from app.helpers.constants import ResponseMessageKeys
import boto3
from botocore.client import Config
from flask import Flask
from flask import jsonify
from flask_limiter import Limiter
from flask_limiter import RequestLimit
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_swagger_ui import get_swaggerui_blueprint
import redis
from rq import Queue
from rq_scheduler import Scheduler
import yaml

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
media_dir = os.path.join(base_dir, 'media')  # type: ignore  # noqa: FKA100
if not os.path.exists(media_dir):
    os.makedirs(media_dir)


try:
    CONFIG_FILE = os.path.join(base_dir, 'config', 'config.yml')  # type: ignore  # noqa: FKA100
    with open(file=CONFIG_FILE) as config_file:
        config_data = yaml.load(config_file, Loader=yaml.FullLoader)

except Exception as exception_error:
    logging.error('Unable to read config file for database : '
                  + str(exception_error))

SHELL_COMMAND_TO_FETCH_TASK_ID = 'curl -s "$ECS_CONTAINER_METADATA_URI_V4/task" | jq -r ".TaskARN" | cut -d "/" -f 3'
TASK_ID = subprocess.getoutput(SHELL_COMMAND_TO_FETCH_TASK_ID)
S3_RESOURCE = boto3.resource(
    's3',
    region_name=config_data.get('AWS').get('S3_REGION'),
    config=Config(signature_version='s3v4')
)

# Initializing logging configuration object
formatter = logging.Formatter(
    '%(asctime)s: %(levelname)s {%(filename)s:%(lineno)d} -> %(message)s'
)

logger = logging.getLogger(__name__)

handler = TimedRotatingFileHandler(
    config_data.get('LOG_FILE_PATH'),
    when='midnight',
    interval=1,
    backupCount=7)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def ratelimit_handler(request_limit: RequestLimit) -> tuple:
    """
        This method will create custom json response for error 429 (Too Many Requests).
    """
    limit_string = request_limit.limit.limit
    time_limit = str(limit_string).split('per')[1]
    # Here, we get limit value in string like 1 per 30 seconds so, for getting time limit we are splitting above string.
    return jsonify({'status': False,
                    'message': ResponseMessageKeys.PLEASE_TRY_AFTER_SECONDS.value.format(time_limit)}), HttpStatusCode.TOO_MANY_REQUESTS.value


def create_app():
    """
    Create a Flask application instance. Register blueprints and updates celery configuration.

        :return: application instance
    """
    try:
        application = Flask(__name__, instance_relative_config=True)
        application.config.from_object(config_data)
        # if TESTING:
        #     application.config.update({
        #     'SQLALCHEMY_DATABASE_URI': config_data.get('SQLALCHEMY_TEST_DATABASE_URI')
        #     })
        # Global error handler for error code 429 (Too Many Requests)
        application.register_error_handler(429, ratelimit_handler)  # type: ignore  # noqa: FKA100
        app_set_configurations(application=application,
                               config_data=config_data)
        initialize_extensions(application)
        register_blueprints(application)
        register_swagger_blueprints(application)

        return application

    except Exception as exception_error:
        logger.error('Unable to create flask app instance : '
                     + str(exception_error))


def initialize_extensions(application):
    """
    Initialize extensions.
    :param application:
    :return:
    """
    try:
        db.init_app(application)
        migrate = Migrate(app=application, db=db, compare_type=True)
        return db, migrate

    except Exception as exception_error:
        logger.error('Unable to initialize extensions : '
                     + str(exception_error))


def register_blueprints(application):
    """
    Registers blueprints.
    :param application:
    :return: None
    """
    try:
        from app.views import v1_blueprints
        application.register_blueprint(v1_blueprints, url_prefix='/api/v1')

    except Exception as exception_error:
        trace = traceback.extract_tb(sys.exc_info()[2])
        # Add the event to the log
        output = 'Unable to register blueprints: %s.\n' % (exception_error)
        output += '\tTraceback is:\n'
        for (file, linenumber, affected, line) in trace:
            output += '\t> Error at function %s\n' % (affected)
            output += '\t  At: {}:{}\n'.format(file, linenumber)
            output += '\t  Source: %s\n' % (line)
        output += '\t> Exception: %s\n' % (exception_error)
        logger.error('Exception Stack Trace')
        logger.error(output)
        logger.error('=========END=========')


def register_swagger_blueprints(application):
    """
    Registers swagger blueprints.
    :param application:
    :return: None
    """
    try:
        swagger_url = '/api-docs/'
        api_url = '/static/swagger_json/{}.json'.format(
            config_data.get('SWAGGER_FILE_NAME'))
        swagger_config = {'app_name': 'Boiler_plate', 'deepLinking': False, }
        swagger_blueprint = get_swaggerui_blueprint(
            base_url=swagger_url,
            api_url=api_url,
            config=swagger_config
        )
        application.register_blueprint(
            swagger_blueprint, url_prefix=swagger_url)

    except Exception as exception_error:
        logger.error('Unable to register blueprints : '
                     + str(exception_error))


def app_set_configurations(application, config_data):
    """This method is used to setting configuration data from config.yml"""
    try:
        for config in config_data:
            application.config[config] = config_data[config]

    except Exception as exception_error:
        logger.error('problem setting app configuration : '
                     + str(exception_error))


def clear_scheduler():
    """ Method to delete scheduled jobs in scheduler. """
    scheduler = Scheduler(connection=r)
    for job in scheduler.get_jobs():
        scheduler.cancel(job)


app = Flask(__name__)
app_set_configurations(application=app, config_data=config_data)
db = SQLAlchemy(app, session_options={'expire_on_commit': False})
migrate = Migrate(app=app, db=db, compare_type=True)
# CORS(app, resources={r'/api/*': {'origins': '*'}})
r = redis.Redis(host=config_data.get('REDIS').get('HOST'), port=config_data.get(
    'REDIS').get('PORT'), db=config_data.get('REDIS').get('DB'))
send_mail_q = Queue(QueueName.SEND_MAIL, connection=r)

clear_scheduler()

limiter = Limiter(app=app, key_func=None, strategy=config_data.get('STRATEGY'),  # Creating instance of Flask-Limiter for rate limiting.
                  key_prefix=config_data.get('KEY_PREFIX'), storage_uri='redis://{}:{}/{}'.format(
    config_data.get('REDIS').get('HOST'), config_data.get('REDIS').get('PORT'), config_data.get('RATE_LIMIT').get('REDIS_DB')))
