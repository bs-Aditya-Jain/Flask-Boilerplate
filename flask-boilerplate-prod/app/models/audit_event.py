from datetime import datetime

from app.helpers.constants import DatabaseAction
from app.models.audit_log import AuditLog
from sqlalchemy import event
from sqlalchemy import inspect
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.attributes import get_history


class AuditableEvent:
    """ Allow a model to be automatically audited """

    @staticmethod
    def create_audit(connection, object_type, object_id, action, state_before=None, state_after=None):
        """ Method to create audit log """
        audit = AuditLog(
            table_name=object_type,
            object_id=object_id,
            action=action,
            state_before=state_before,
            state_after=state_after
        )
        audit.save(connection)

    @classmethod
    def __declare_last__(cls):
        """ Declare database events on which audit has to listen """
        event.listen(cls, 'after_insert', cls.audit_insert)  # noqa: FKA100
        event.listen(cls, 'after_delete', cls.audit_delete)  # noqa: FKA100
        event.listen(cls, 'after_update', cls.audit_update)  # noqa: FKA100

    @staticmethod
    def audit_insert(mapper, connection, target):  # noqa: F841
        """Listen for the `after_insert` event and create an AuditLog entry"""
        state_after = {}
        attrs = class_mapper(target.__class__).column_attrs
        for attr in attrs:
            state_after[attr.key] = getattr(target, attr.key)
        obj_as_dict = AuditableEvent.convert_obj_to_dict(target)
        state_after = AuditableEvent.dict_remove_datetime(state_after)

        target.create_audit(connection=connection, object_type=target.__tablename__,
                            object_id=target.id if obj_as_dict.get(
                                'id') else target.uuid,
                            action=DatabaseAction.CREATE.value, state_before={}, state_after=state_after)

    @staticmethod
    def audit_delete(mapper, connection, target):  # noqa: F841
        """Listen for the `after_delete` event and create an AuditLog entry"""
        obj_as_dict = AuditableEvent.convert_obj_to_dict(target)
        target.create_audit(connection=connection, object_type=target.__tablename__,
                            object_id=target.id if obj_as_dict.get(
                                'id') else target.uuid,
                            action=DatabaseAction.DELETE.value)

    @staticmethod
    def dict_remove_datetime(data):
        """
            This method checks for datetime objecy in dictionary and converts it to string.
        """
        return {key: value.strftime('%Y/%m/%d %H:%M:%S') if isinstance(value, datetime) else value for (key, value)
                in data.items()}

    @staticmethod
    def convert_obj_to_dict(obj):
        """
            This method converts given model object to dictionary.
        """
        return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}

    @staticmethod
    def audit_update(mapper, connection, target):  # noqa: F841
        """ Listen for the `after_update` event and create an AuditLog entry with before and after state changes"""
        state_before = {}
        state_after = {}
        inspr = inspect(target)
        attrs = class_mapper(target.__class__).column_attrs
        for attr in attrs:
            hist = getattr(inspr.attrs, attr.key).history
            if hist.has_changes():
                try:
                    state_before[attr.key] = get_history(target, attr.key)[2].pop()  # noqa: FKA100
                except Exception:
                    state_before[attr.key] = get_history(target, attr.key)[2]  # noqa: FKA100
                state_after[attr.key] = getattr(target, attr.key)
        state_before = AuditableEvent.dict_remove_datetime(state_before)
        state_after = AuditableEvent.dict_remove_datetime(state_after)
        obj_as_dict = AuditableEvent.convert_obj_to_dict(target)
        if state_after != state_before:
            target.create_audit(connection=connection, object_type=target.__tablename__,
                                object_id=target.id if obj_as_dict.get(
                                    'id') else target.uuid,
                                action=DatabaseAction.UPDATE.value,
                                state_before=state_before, state_after=state_after)
