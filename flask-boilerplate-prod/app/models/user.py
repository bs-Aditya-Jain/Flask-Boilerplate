"""Contains user table definitions."""
from __future__ import annotations

from typing import Any

from app import db
from app.helpers.constants import SortingOrder
from app.models.base import Base
from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy.ext import hybrid


class User(Base):
    """Stores only personal details related to user like first name, last name, primary email, primary phone,
    country code, pin, device tokens, etc."""
    __tablename__ = 'user'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String, nullable=True)
    primary_email = db.Column(db.String, nullable=False, unique=True)
    primary_phone = db.Column(db.String, nullable=False)
    country_code = db.Column(db.String, nullable=True)
    pin = db.Column(db.String, nullable=True)
    auth_token = db.Column(db.String, nullable=True)
    last_login_at = db.Column(db.DateTime)
    address = db.Column(db.Text)
    zip_code = db.Column(db.String)
    deactivated_at = db.Column(db.DateTime)
    deleted_at = db.Column(db.DateTime)
    created_by = db.Column(db.BigInteger)
    updated_by = db.Column(db.BigInteger)

    # org = relationship(Organization)

    @hybrid.hybrid_property
    def full_name(self) -> str:
        """Return full name."""
        if self.last_name:
            return self.first_name + ' ' + self.last_name
        return self.first_name

    @staticmethod
    def get_all() -> list:
        """Return user table all records."""
        return db.session.query(User).all()

    @staticmethod
    def get_all_user_detail() -> dict:
        """Return all records with basic details from user table."""
        query = db.session.query(User.id, User.first_name, User.full_name, User.last_name, User.primary_email,  # type: ignore  # noqa: FKA100
                                 User.country_code, User.primary_phone).all()
        return {r.id: r._asdict() for r in query}

    @classmethod
    def serialize_user(cls, details: list) -> list:
        """ Make a list of User objects for crew members."""
        data = []
        for single_data in details:
            single_data_obj = {
                'id': single_data.id,
                'address': single_data.address,
                'zip_code': single_data.zip_code,
                'name': single_data.full_name,
                'first_name': single_data.first_name,
                'last_name': single_data.last_name,
                'email': single_data.primary_email,
                'phone': single_data.primary_phone,
                'country_code': single_data.country_code,
                'deactivated_at': single_data.deactivated_at if single_data.deactivated_at else '',
                'deleted_at': single_data.deleted_at,
                'created_at': single_data.created_at,
                'updated_at': single_data.updated_at,
            }

            data.append(single_data_obj)

        return data

    @classmethod
    def get_by_email(cls, email: str) -> Any:
        """Filter records by email."""
        return db.session.query(User).filter(User.primary_email == email).first()

    @staticmethod
    def get_user_list(org_id: Any = None, q: Any = None, sort: Any = None, page: Any = None, size: Any = None) -> str:
        """Filter records by query params and sorts them based on page, size,
        sort(sorting parameter)."""
        if sort == SortingOrder.ASC.value:
            query = db.session.query(User).filter(
                User.deleted_at == None).order_by(asc(User.created_at))
        else:
            query = db.session.query(User).filter(
                User.deleted_at == None).order_by(desc(User.created_at))
        if q:
            query = query.filter(User.full_name.ilike('%{}%'.format(q)))
        if page and size:
            offset = (int(page) - 1) * int(size)
            query = query.limit(size)
            query = query.offset(offset)
        return query
