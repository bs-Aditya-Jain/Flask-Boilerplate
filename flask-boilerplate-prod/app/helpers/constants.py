"""All the constants which is used in project is defined in this file."""
import enum


class EnumBase(enum.Enum):
    """Base class for all enums with common method"""
    @classmethod
    def get_name(cls, status):
        """Returns the name of each item in enum"""
        for name, member in cls.__members__.items():
            if member.value == status:
                return str(member.value)
        return None


class Methods(enum.Enum):
    """ http methods used"""
    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    DELETE = 'DELETE'


class HttpStatusCode(enum.Enum):
    """Enum for storing different http status cocde."""
    OK = '200'
    BAD_REQUEST = '400'
    UNAUTHORIZED = '401'
    FORBIDDEN = '403'
    NOT_FOUND = '404'
    INTERNAL_SERVER_ERROR = '500'
    TOO_MANY_REQUESTS = '429'

    @classmethod
    def get_name(cls, status):
        """This method returns key name of enum from value."""
        if status == cls.OK.value:
            return 200
        elif status == cls.BAD_REQUEST.value:
            return 400
        elif status == cls.UNAUTHORIZED.value:
            return 401
        elif status == cls.FORBIDDEN.value:
            return 403
        elif status == cls.INTERNAL_SERVER_ERROR.value:
            return 500
        else:
            return None


class ResponseMessageKeys(enum.Enum):
    """API response messages for various purposes"""

    INVALID_TOKEN = 'Invalid Token.'
    TOKEN_EXPIRED = 'Token Expired, Try sign in again.'
    ENTER_CORRECT_INPUT = 'Enter correct input.'
    LOGIN_SUCCESSFULLY = 'Hi {0}, great to see you!'
    LOGIN_FAILED = 'Login Failed.'
    LOGOUT_SUCCESSFULLY = 'Logout Successfully.'
    PLEASE_TRY_AFTER_SECONDS = 'Request limit reached: Please try after {0}s'
    INVALID_FILE_TYPE = '{0} should be of {1} formats only.'
    SUCCESS = 'Details Fetched Successfully.'
    FAILED = 'Something went wrong.'
    INVALID_PASSWORD = 'Invalid password.'
    USER_NOT_EXIST = 'Entered Email ID is not registered with us.'
    EMAIL_DETAILS_NOT_FOUND = 'Entered Email ID is not registered with us.'


SupportedFileTypes = {  # Contains all the supported file types.
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'jpg': 'image/jpg',
    'pdf': 'application/pdf'
}


class TimeInSeconds(EnumBase):
    """Enum that will return time in seconds from different keys. (ex.Five_MIN=300)"""
    FIVE_MIN = 300
    THIRTY_MIN = 1800
    SIXTY_MIN = 3600
    TWENTY_FOUR_HOUR = 86400
    TWO_DAYS = 172800
    ONE_MONTH = 2592000


class DataLevel(EnumBase):
    """Data level for serializer status enum"""
    INFO = 'INFO'
    DETAIL = 'DETAIL'


class ValidationMessages(enum.Enum):
    """ Validation messages for different fields."""
    EMAIL = 'Please Enter Email ID.'
    FIRST_NAME = 'First name is mandatory to add.'
    LAST_NAME = 'Last name is mandatory to add.'
    ADDRESS = 'Address is mandatory to add.'
    PHONE = 'Phone number is mandatory to add.'
    PHONE_INVALID = 'Please enter valid phone number.'
    COUNTRY_CODE = 'Country code is mandatory to select.'
    COUNTRY_CODE_INVALID = 'Please enter valid country code.'
    COUNTRY = 'Country is mandatory to add.'
    CITY = 'City one is mandatory to add.'
    PINCODE = 'PostalCode is mandatory to add.'
    NAME = 'Name is mandatory to add.'


class QueueName:
    """redis queue scheduler names"""
    SEND_MAIL = 'SEND_MAIL'


class EmailTypes(enum.Enum):
    """Enum for storing different Email Types."""
    INVITE = 'invite'


class EmailSubject(enum.Enum):
    """Emails subject's texts"""
    WELCOME_TO_PROJECT = "You're invited as a Boiler Plate User!"


class SortingOrder(EnumBase):
    """Enum for storing sorting parameters value."""
    ASC = 'asc'
    DESC = 'desc'


class SortingParams(EnumBase):
    """Enum for storing transactions."""
    AMOUNT = 'AMOUNT'
    DATE = 'DATE'
    NAME = 'NAME'
    TITLE = 'TITLE'


class DatabaseAction(enum.Enum):
    """
        Database operation names.
    """
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'
    READ = 'read'
