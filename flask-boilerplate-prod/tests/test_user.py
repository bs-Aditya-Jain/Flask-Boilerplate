"""
    This file contains the test cases for the user module.
"""
import json

from app.helpers.constants import ResponseMessageKeys
from app.models.user import User
from app.views.user_view import UserView
import pytest
from tests.conftest import validate_response
from tests.conftest import validate_status_code


@pytest.mark.run(order=1)
def test_login(user_client):
    """    TEST CASE: Admin/Initial User Login.
        """
    data = {
        'email': 'admin@project.com',
        'pin': '12345'
    }
    auth_user = User.get_by_email('admin@project.com')
    expected_response = UserView.create_auth_response(
        self=None, user=auth_user, data=None)
    expected_response['details'].update(created_at='*')
    expected_response['details'].update(updated_at='*')

    api_response = user_client.post(
        '/api/v1/user/auth', json=data, content_type='application/json'
    )
    expected_response = {
        'data': expected_response
    }
    expected_response.update(
        message=ResponseMessageKeys.LOGIN_SUCCESSFULLY.value.format('InitialUser'))
    expected_response.update(status=True)
    actual_response = json.loads(
        api_response.get_data())
    user_client.environ_base['x-access-token'] = json.loads(
        api_response.get_data()).get('data').get('token')
    assert validate_status_code(
        expected=200, received=api_response.status_code)
    assert validate_response(
        expected=expected_response, received=actual_response)


@pytest.mark.run(order=2)
def test_login_with_wrong_pin(user_client):
    """
            TEST CASE: Super Admin Login with wrong pin.
        """
    data = {
        'email': 'admin@project.com',
        'pin': '123456'
    }
    expected_response = {'message': ResponseMessageKeys.INVALID_PASSWORD.value,
                         'status': False}

    api_response = user_client.post(
        '/api/v1/user/auth', json=data, content_type='application/json'
    )
    assert validate_status_code(
        expected=403, received=api_response.status_code)
    assert validate_response(
        expected=expected_response, received=json.loads(
            api_response.get_data()))
