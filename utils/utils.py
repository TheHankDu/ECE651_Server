from datetime import datetime
import functools
import logging
import random
import string

from flask import jsonify

logger = logging.getLogger(__name__)


def get_timestamp(t=None):
    dt = t if t else datetime.utcnow()
    return dt.isoformat() + 'Z'


def parse_timestamp(timestamp):
    if timestamp.endswith('Z'):
        timestamp = timestamp[:-1]
    return datetime.fromisoformat(timestamp)


def exception_handler(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            logger.exception("There was an exception in {}. Error information: {}".format(function.__name__, e))
            return jsonify({
                'success': 0
            }), 500

    return wrapper


def random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
