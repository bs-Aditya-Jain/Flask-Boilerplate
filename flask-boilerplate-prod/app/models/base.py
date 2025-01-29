"""Contains some basic definitions that can be extended by other models."""
from datetime import datetime
from typing import Any

from app import db
from app.helpers.constants import SortingOrder
from app.models.audit_event import AuditableEvent
from dateutil import tz
from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy.orm import Query


class Base(db.Model, AuditableEvent):
    """Base model for all other models that contains some basic methods that can be extended by other modals."""
    __abstract__ = True
    uuid = db.Column(db.String, unique=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=datetime.now(tz=tz.tzlocal()))
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=datetime.now(tz=tz.tzlocal()), onupdate=datetime.now(tz=tz.tzlocal()))

    @classmethod
    def get_by_id(cls, id: int) -> Any:
        """Filter record by id."""
        return db.session.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_by_uuid(cls, uuid: str) -> Any:
        """Filter record by uuid. """
        return db.session.query(cls).filter(cls.uuid == uuid).first()

    @classmethod
    def get_by_slug(cls, slug: str) -> Any:
        """Filter record by slug."""
        return db.session.query(cls).filter(cls.slug == slug).first()

    @classmethod
    def delete_by_uuid(cls, uuid: str) -> None:
        """Delete record by uuid."""
        db.session.query(cls).filter(cls.uuid == uuid).delete()
        db.session.commit()

    @classmethod
    def update_property_by_id(cls, id: int, property: str, new_value: Any) -> None:
        """Updates record's property with new value by id."""
        query = db.session.query(cls).filter(cls.id == id)
        query.update({property: new_value})
        db.session.commit()

    @classmethod
    def search(cls, q: Any = None, sort: Any = None, page: Any = None, size: Any = None) -> Query:
        """Filter records by query params and sorts them based on page, size,
        sort(sorting parameter)."""
        if sort == SortingOrder.ASC.value:
            query = db.session.query(cls).order_by(asc(cls.created_at))
        else:
            query = db.session.query(cls).order_by(desc(cls.created_at))
        if q:
            query = query.filter(cls.name.ilike('%{}%'.format(q)))
        if page and size:
            offset = (int(page) - 1) * int(size)
            query = query.limit(size)
            query = query.offset(offset)
        return query
