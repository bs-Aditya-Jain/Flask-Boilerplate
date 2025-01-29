"""
    Database model for storing audit logs in database is written in this File along with its methods.
"""
from datetime import datetime
from typing import Any

from app import db
from app import logger
from app.helpers.constants import DataLevel
from app.helpers.constants import SortingOrder
from dateutil import tz


class AuditLog(db.Model):
    """ An audit log for other model's actions """
    __tablename__ = 'audit_log'

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger)
    table_name = db.Column(db.Text, nullable=False)
    object_id = db.Column(db.String)
    action = db.Column(db.String)
    state_before = db.Column(db.JSON)
    state_after = db.Column(db.JSON)
    method = db.Column(db.String)
    url = db.Column(db.String)
    headers = db.Column(db.JSON)
    body = db.Column(db.JSON)
    args = db.Column(db.JSON)
    ip = db.Column(db.String)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=datetime.now(tz=tz.tzlocal()))
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=datetime.now(tz=tz.tzlocal()))

    @classmethod
    def get_request_info(cls):
        """
            This method is used to access request.
            - if database action is performed using api, it will return request as it is.
            - if database action is perform without api [e.g. insert from testing without api call'],
                then it will set request with empty values as request is not present at that time.
        """
        try:
            """ Return request if access  """
            from flask import request
            hasattr(request, 'user')
            return request
        except Exception:
            from types import SimpleNamespace
            from werkzeug.datastructures import ImmutableMultiDict
            request = {'headers': {},
                       'method': None,
                       'url': '',
                       'args': ImmutableMultiDict(),  # immutable dict
                       'form': ImmutableMultiDict(),  # immutable dict
                       }
            return SimpleNamespace(**request)

    @classmethod
    def get_user_id(cls, request):
        """ Method to get user id if exists for request """
        if hasattr(request, 'user_id'):
            return request.user_id
        else:
            return None

    @classmethod
    def get_by_id(cls, id: int) -> Any:
        """Filter record by id."""
        return db.session.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_request_body(cls, request):
        """ Method to get request body """
        body = {}

        try:
            body = request.get_json(force=True)
        except Exception:
            body = request.form.to_dict(flat=False)

        return body

    def __init__(self, table_name, object_id, action, state_before, state_after):
        """ Initialize audit_log object """
        request = AuditLog.get_request_info()
        try:
            if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
                client_ip = request.environ['REMOTE_ADDR']
            else:
                client_ip = str(request.environ.get(
                    'HTTP_X_FORWARDED_FOR')).split(',')[0].strip()
        except Exception as exception_error:
            logger.error(f'Failed to Get Client IP - > {exception_error}')
            client_ip = ''
        self.user_id = AuditLog.get_user_id(request)
        self.table_name = table_name
        self.object_id = object_id
        self.action = action
        self.state_before = state_before
        self.state_after = state_after
        self.method = request.method
        self.url = request.url
        self.headers = dict(request.headers.items())
        self.body = AuditLog.get_request_body(request)
        self.args = request.args.to_dict(flat=False)
        self.ip = client_ip  # pylint: disable=C0103

    def __repr__(self):
        """
            Object Representation Method for custom object representation on console or log
        """
        return '<AuditLog %r: %r -> %r>' % (self.user_id, self.table_name, self.action)

    def save(self, connection):
        """ Insert data into table """

        connection.execute(
            self.__table__.insert(),
            user_id=self.user_id,
            table_name=self.table_name,
            object_id=self.object_id,
            action=self.action,
            state_before=self.state_before,
            state_after=self.state_after,
            method=self.method,
            url=self.url,
            headers=self.headers,
            body=self.body,
            args=self.args,
            ip=self.ip
        )

    @classmethod
    def get_logs(cls, action: Any = None, user_id: Any = None,
                 page: Any = None, pagination: Any = None, sort: Any = None,
                 start_date: Any = None, end_date: Any = None):
        """ Collect audit logs from table """
        query = db.session.query(cls)

        if action:
            query = query.filter(cls.action.in_(action))

        if user_id:
            query = query.filter(cls.user_id.in_(user_id))

        if start_date:
            query = query.filter(cls.created_at >= start_date)

        if end_date:
            query = query.filter(cls.created_at <= end_date)

        if sort == SortingOrder.ASC.value:
            query = query.order_by(cls.id.asc())
        else:
            query = query.order_by(cls.id.desc())

        if page and pagination and sort:
            offset = (int(page) - 1) * int(pagination)
            query = query.limit(pagination)
            query = query.offset(offset)

        return query

    @classmethod
    def serialize(cls, audit_logs: list, data_level: str = DataLevel.INFO.value, user_dict: Any = None) -> list:
        """ Make a list of Audit Log objects."""
        data = []
        for audit_log in audit_logs:
            if data_level == DataLevel.INFO.value:
                data_dict = {
                    'id': audit_log.id,
                    'user_id': audit_log.user_id,
                    'table_name': audit_log.table_name,
                    'action': audit_log.action,
                    'ip': audit_log.ip,
                    'created_at': audit_log.created_at
                }
            if data_level == DataLevel.DETAIL.value:
                data_dict = {

                    'user_name': user_dict[audit_log.user_id]['full_name'] if audit_log.user_id else '',
                    'table_name': audit_log.table_name.replace('_', ' '),  # type: ignore  # noqa: FKA100
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
            data.append(data_dict)
        return data
