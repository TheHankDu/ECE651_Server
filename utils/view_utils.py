from functools import wraps
import logging

from bson import ObjectId
from flask import jsonify, request

from db import dbutils
from db.models import CourseToStudent, CourseToTeacher
from utils import error_msg
from utils.login_utils import get_current_user


logger = logging.getLogger(__name__)


def get_val_from_req(field_name):
    if request.method == 'GET':
        field = request.args.get(field_name)
    else:
        field = request.form[field_name]
    return field


def _req_field_exists_in_db(model, field_name, field_name_in_db, field_type):
    field = get_val_from_req(field_name)
    if not field_type:
        res = dbutils.exists(model, {field_name_in_db: field})
    else:
        res = dbutils.exists(model, {field_name_in_db: field_type(field)})
    logger.debug('Checking if {}:{}:{} exists: {}'.format(
        model.__name__, field_name_in_db, field, res))
    return res


def ensure_exists(model, field_name, field_name_in_db, error_msg, field_type=None):
    def wrapper(f):
        @wraps(f)
        def check():
            if _req_field_exists_in_db(model, field_name, field_name_in_db if field_name_in_db else field_name, field_type):
                return f()
            else:
                return jsonify({
                    'success': 0,
                    'msg': error_msg
                }), 404
        return check
    return wrapper


def ensure_not_exists(model, field_name, field_name_in_db, error_msg, field_type=None):
    def wrapper(f):
        @wraps(f)
        def check():
            if not _req_field_exists_in_db(model, field_name, field_name_in_db if field_name_in_db else field_name, field_type):
                return f()
            else:
                return jsonify({
                    'success': 0,
                    'msg': error_msg
                }), 409
        return check
    return wrapper


def ensure_user_in_course(f):
    @wraps(f)
    def check():
        user = get_current_user()
        query = {'course_id': ObjectId(get_val_from_req('course_id'))}
        if user.type == 'teacher':
            query['teacher_id'] = user._id
            model = CourseToTeacher
            e = error_msg.TEACHER_NOT_IN_CLASS
        elif user.type == 'student':
            query['student_id'] = user._id
            model = CourseToStudent
            e = error_msg.STUDENT_NOT_IN_CLASS
        if not dbutils.exists(model, query):
            return jsonify({
                'success': 0,
                'msg': e
            }), 403
        return f()
    return check
