"""common view functions required by all modules"""
from datetime import datetime
import os

from app import config_data
from app import logger
from app.helpers.constants import HttpStatusCode
from app.helpers.constants import ResponseMessageKeys
from app.helpers.constants import SupportedFileTypes
from app.helpers.decorators import api_time_logger
from app.helpers.decorators import token_required
from app.helpers.utility import required_validator
from app.helpers.utility import send_json_response
from app.models.audit_log import AuditLog
from app.models.user import User
from flask import request
from flask.views import View
from magic import Magic
from workers.s3_worker import get_presigned_url
from workers.s3_worker import upload_file_and_get_object_details


class FileView(View):
    """Contains file upload view"""
    @api_time_logger
    @token_required
    def dispatch_request(self, logged_in_user: User) -> tuple:
        """Adds/ Uploads file to s3 """
        data = request.files
        required_fields = ['upload']
        is_valid = required_validator(
            request_data=data, required_fields=required_fields)
        if is_valid['is_error']:
            return send_json_response(http_status=HttpStatusCode.BAD_REQUEST.value, response_status=False,
                                      message_key=ResponseMessageKeys.ENTER_CORRECT_INPUT.value, data=None,
                                      error=is_valid['data'])

        uploaded_file = data.get('upload')
        temp_path = os.path.join(config_data['UPLOAD_FOLDER'], uploaded_file.filename)  # type: ignore  # noqa: FKA100
        uploaded_file.save(temp_path)
        content_type = Magic(mime=True).from_file(temp_path)
        if content_type not in SupportedFileTypes.values():
            os.remove(temp_path)
            return send_json_response(http_status=HttpStatusCode.BAD_REQUEST.value, response_status=False,
                                      message_key=ResponseMessageKeys.ENTER_CORRECT_INPUT.value, data=None,
                                      error={
                                          'upload': ResponseMessageKeys.INVALID_FILE_TYPE.value.format(   # type: ignore  # noqa: FKA100
                                              'Upload', list(SupportedFileTypes.keys()))
                                      })
        name, path, size = upload_file_and_get_object_details(
            file_obj=uploaded_file, temp_path=temp_path)

        upload_path = get_presigned_url(
            path=path)
        return send_json_response(http_status=HttpStatusCode.OK.value, response_status=True,
                                  message_key=ResponseMessageKeys.SUCCESS.value,
                                  data={'uploaded_file_path': upload_path}, error=None)


class AuditView(View):
    """Contains all views for accessing audit logs"""
    @staticmethod
    @api_time_logger
    @token_required
    def list(logged_in_user: User) -> tuple:
        """
        Returns list of audit logs with details like user_name, table_name, ip_address, etc. from audit log table.
        """
        page = request.args.get(key='page', default=None)
        pagination = request.args.get(key='pagination', default=None)
        sort = request.args.get(key='sort', default=None)
        user_id = request.args.get(key='user_id', default=None)
        action = request.args.get(key='action', default=None)
        start_date = request.args.get(key='start_date', default=None)
        end_date = request.args.get(key='end_date', default=None)
        user_ids = []
        if user_id:
            try:
                user_dict = user_id.split(',')
                user_ids = []
                for user_id in user_dict:
                    if user_id:
                        user_ids.append(int(user_id))

            except Exception as error:
                logger.error(
                    'Error while fetching Audit Log details : {}'.format(error))
                return send_json_response(http_status=HttpStatusCode.BAD_REQUEST.value, response_status=False,
                                          message_key=ResponseMessageKeys.ENTER_CORRECT_INPUT.value, data=None,
                                          error={
                                              'user_id': 'Please enter valid user_id.'
                                          })

        if action:
            try:
                action = action.split(',')
            except Exception as error:
                logger.error(
                    'Error while fetching Audit Log details : {}'.format(error))
                return send_json_response(http_status=HttpStatusCode.BAD_REQUEST.value, response_status=False,
                                          message_key=ResponseMessageKeys.ENTER_CORRECT_INPUT.value, data=None,
                                          error={
                                              'action': 'Please enter valid action.'
                                          })

        if start_date:
            try:
                start_date = datetime.strptime(start_date + 'T00:00:00',        # type: ignore  # noqa: FKA100
                                               '%d/%m/%YT%H:%M:%S')
            except Exception as error:
                logger.error(
                    'Error while fetching Audit Log details : {}'.format(error))
                logger.error('Error while fetching Audit Log details for user id  : {}'.format(
                    logged_in_user.id))
                return send_json_response(http_status=HttpStatusCode.BAD_REQUEST.value, response_status=False,
                                          message_key=ResponseMessageKeys.ENTER_CORRECT_INPUT.value, data=None,
                                          error={
                                              'start_date': 'Please enter valid start_Date.'
                                          })
        if end_date:
            try:
                end_date = datetime.strptime(end_date + 'T23:59:59',    # type: ignore  # noqa: FKA100
                                             '%d/%m/%YT%H:%M:%S')
            except Exception as error:
                logger.error(
                    'Error while fetching Audit Log details : {}'.format(error))
                return send_json_response(http_status=HttpStatusCode.BAD_REQUEST.value, response_status=False,
                                          message_key=ResponseMessageKeys.ENTER_CORRECT_INPUT.value, data=None,
                                          error={
                                              'end_date': 'Please enter valid end_date.'
                                          })
        audit_logs = AuditLog.get_logs(sort=sort, page=page, pagination=pagination, action=action,
                                       user_id=user_ids, start_date=start_date, end_date=end_date)

        current_page_count = audit_logs.count()
        audit_logs = audit_logs.all()
        user_dict = User.get_all_user_detail()
        audit_log_list = AuditLog.serialize(audit_logs=audit_logs)

        total_count = AuditLog.get_logs(
            action=action, user_id=user_id, start_date=start_date, end_date=end_date).count()
        data = {'result': audit_log_list, 'objects': {'user': user_dict}, 'current_page_count': current_page_count,
                'current_page': 1 if page is None else int(page),
                'next_page': '' if page is None else int(page) + 1,
                'total_count': total_count} if current_page_count > 0 else None

        return send_json_response(http_status=HttpStatusCode.OK.value, response_status=True,
                                  message_key=ResponseMessageKeys.SUCCESS.value, data=data, error=None)

    @staticmethod
    @api_time_logger
    @token_required
    def details(logged_in_user: User) -> tuple:
        """
        Returns audit log details like action, args, body, created_at, headers, ip, method, object_id, etc.
        from audit log table of the passed id.
        """

        audit_log_id = request.args.get(key='id', default=None)
        if audit_log_id is None:
            return send_json_response(http_status=HttpStatusCode.BAD_REQUEST.value, response_status=False, message_key=ResponseMessageKeys.ENTER_CORRECT_INPUT.value, data=None, error={
                'audit_log_id': 'audit_log_id is required.'
            })

        audit_log = AuditLog.get_by_id(int(audit_log_id))
        user = ''
        if audit_log:
            if audit_log.user_id:
                user = User.get_by_id(audit_log.user_id)
            data_dict = {
                'id': audit_log.id,
                'user_name': user.full_name if user else user,
                'object_id': audit_log.object_id,
                'action': audit_log.action,
                'state_before': audit_log.state_before,
                'state_after': audit_log.state_after,
                'method': audit_log.method,
                'url': audit_log.url,
                'headers': audit_log.headers,
                'body': audit_log.body,
                'args': audit_log.args,
                'ip': audit_log.ip,
                'created_at': audit_log.created_at
            }

        if audit_log is None:
            logger.error('Error while fetching Audit Log details for user id  : {}'.format(
                logged_in_user.id))
            return send_json_response(http_status=HttpStatusCode.OK.value, response_status=False,
                                      message_key=ResponseMessageKeys.EMAIL_DETAILS_NOT_FOUND.value, data=None, error=None)
        return send_json_response(http_status=HttpStatusCode.OK.value, response_status=True,
                                  message_key=ResponseMessageKeys.SUCCESS.value, data={'api_log_data': data_dict}, error=None)
