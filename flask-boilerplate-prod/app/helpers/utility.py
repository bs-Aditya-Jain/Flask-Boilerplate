"""Common methods is defined here."""
from datetime import datetime
from datetime import timezone
import math
import random
from random import randint
import re
import string
from typing import Any

from app import config_data
from app.helpers.constants import ValidationMessages
from flask import jsonify
from hashids import Hashids
import jwt

hash_id = Hashids(min_length=7, salt=config_data.get('HASH_ID_SALT'))


def days_to_seconds(days: int) -> int:
    seconds = 86400 * days  # 24 * 60 * 60 * days
    return seconds


def generate_random_string(length: int) -> str:
    """generates a random string of length"""
    # initializing size of string
    random_string_length = length

    # using random.choices()
    # generating random strings
    res = ''.join(random.choices(
        string.ascii_lowercase, k=random_string_length))

    return res


def generate_random_number_string(length: int) -> str:
    """generates a random string of length"""
    # initializing size of string
    random_string_length = length

    # using random.choices()
    # generating random strings
    res = ''.join(random.choices('123456789', k=random_string_length))

    return res


TYPE_NAMES = {
    int: 'integer', float: 'float', bool: 'boolean', str: 'string', dict: 'dict', list: 'list'
}


def generate_email_token(id: int, org_id: Any = None) -> bytes:
    """Generates a unique jwt token with id and timestamp to be sent via email for one time use as login link:
    Encodes teh current timestamp and id in jwt"""
    secret = config_data.get('SECRET_KEY')
    current_time = datetime.now(timezone.utc)
    utc_time = current_time.replace(tzinfo=timezone.utc)
    utc_timestamp = utc_time.timestamp()
    data = {
        'timestamp': utc_timestamp,
        'id': id
    }
    token = jwt.encode(payload=data, key=secret)
    # token_string = token.decode('utf-8')
    return token


def random_with_n_digits(num: int) -> int:
    """Generates a random number of length num"""
    range_start = 10 ** (num - 1)
    range_end = (10 ** num) - 1
    return randint(range_start, range_end)  # type: ignore  # noqa: FKA100


def is_token_valid(token: bytes) -> bool:
    """ Returns true if jwt token  is valid"""
    try:
        jwt.decode(jwt=token, key=config_data.get(
            'SECRET_KEY'), algorithms=['HS256'])
        return True
    except Exception as e:  # type: ignore  # noqa: F841
        return False


def field_type_validator(request_data: dict = {}, field_types: dict = {}, prefix: str = '') -> dict:
    """
    Validate given dict of fields and their types:
    Iterates over field_types keys and checks if the values received from the request match the values specified in the api function
    If one does not match it returns and error with the field name
    """
    cleaned_data = {}
    errors = {}
    is_error = False
    for field in field_types.keys():
        field_value = request_data.get(field)

        if field_value is not None:
            field_type = field_types[field]

            if field_type == float:
                try:
                    field_value = float(field_value)
                except Exception as e:  # type: ignore  # noqa: F841
                    pass
            if field_type == int:
                try:
                    field_value = int(field_value)
                except Exception as e:  # type: ignore  # noqa: F841
                    pass
            if field_type == int:
                try:
                    field_value = int(field_value)
                except Exception as e:  # type: ignore  # noqa: F841
                    pass
            if type(field_value) != field_type:
                type_name = TYPE_NAMES.get(field_type, field_type.__name__)  # type: ignore  # noqa: FKA100

                if prefix:
                    message = f'{prefix} {field} should be {type_name} value.'
                else:
                    formatted_field = field.replace('_', ' ').title()  # type: ignore  # noqa: FKA100
                    message = f'{formatted_field} should be {type_name} value.'

                errors[field] = message

                if is_error is False:
                    is_error = True

        cleaned_data[field] = field_value

    return {'is_error': is_error, 'data': errors if is_error else cleaned_data}


def required_validator(request_data: dict = {}, required_fields: list = [], prefix: Any = None,
                       module_name: Any = None) -> dict:
    """
    Validate required fields of given dict of data:
    Iterates over required fields list and checks if that key is present in request
    If one also is not found it returns and error with the field name

    """
    errors = {}
    is_error = False
    for field in required_fields:
        if request_data.get(field) in [None, '']:
            try:
                message = ValidationMessages[field.upper()].value
                if module_name and field == ValidationMessages.NAME.name.lower():
                    message = module_name.replace(  # type: ignore  # noqa: FKA100
                        '_', ' ').capitalize() + ' ' + message
            except Exception:
                if prefix:
                    message = f'{prefix} {field} is required.'
                else:
                    formatted_field = re.sub(r'(_uuids)|(_ids)|(_uuid)|(_id)', '',  # type: ignore  # noqa: FKA100
                                             field)
                    formatted_field = formatted_field.replace('_', ' ').title()  # type: ignore  # noqa: FKA100
                    message = f'{formatted_field} is required.'

            errors[field] = message

            if is_error is False:
                is_error = True

    return {'is_error': is_error, 'data': errors}


def send_json_response(http_status: int, response_status: bool, message_key: str, data: Any = None,
                       error: Any = None) -> tuple:
    """This method used to send JSON response in custom dir structure. Here, status represents boolean value true/false
    and http_status is http response status code."""

    if data is None and error is None:
        return jsonify({'status': response_status, 'message': message_key}), http_status
    if response_status:
        return jsonify({'status': response_status, 'message': message_key, 'data': data}), http_status
    else:
        return jsonify({'status': response_status, 'message': message_key, 'error': error}), http_status


def get_pagination_meta(current_page: int, page_size: int, total_items: int) -> dict:
    """
        This method generates pagination metadata.
    """

    if page_size:
        total_pages = math.ceil(total_items / page_size)
        has_next_page = current_page < total_pages
        has_previous_page = current_page > 1
        next_page = current_page + 1 if has_next_page else None
        previous_page = current_page - 1 if has_previous_page else None
    else:
        total_pages = current_page
        has_next_page = None
        has_previous_page = None
        next_page = None
        previous_page = None
        page_size = None

    return {
        'current_page': current_page,
        'page_size': page_size,
        'total_items': total_items,
        'total_pages': total_pages,
        'has_next_page': has_next_page,
        'has_previous_page': has_previous_page,
        'next_page': next_page,
        'previous_page': previous_page
    }
