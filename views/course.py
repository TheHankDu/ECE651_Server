import logging

from bson import ObjectId
from flask import Blueprint, request, jsonify
from flask_login import login_required
from pymodm.errors import ValidationError

from db.models import Course, User, CourseToStudent, CourseToTeacher
from utils import error_msg
from utils.login_utils import authorize
from utils.login_utils import get_current_user
from utils.utils import get_timestamp
from utils.view_utils import ensure_exists, ensure_not_exists
from .user import filter_public_fields

course = Blueprint('course', __name__)
logger = logging.getLogger(__name__)


@course.route('/create', methods=['POST'])
@login_required
@authorize({'teacher', 'admin'})
@ensure_not_exists(Course, 'course_name', 'course_name', error_msg.DUPLICATE_COURSENAME)
def create_course():
    course_name = request.form['course_name']
    try:
        course = Course(course_name)
        course.save()
        logger.info('course: {} was created successfully'.format(course_name))
        return jsonify({
            'success': 1,
            'course_id': str(course._id),
            'course_name': course_name
        })
    except ValidationError as e:
        logger.warning(
            'Failed to create new course. Exception: {}'.format(e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400


@course.route('/get_all', methods=['GET'])
@login_required
@authorize({'student', 'teacher', 'admin'})
def get_all():
    courses = list(Course.objects.all())
    return jsonify({
        'success': 1,
        'courses': sorted(
            [{
                'course_id': str(c._id),
                'course_name': c.course_name,
                'create_at': get_timestamp(c.create_at)} for c in courses
            ],
            key=lambda x: x['create_at']
        )
    })


@course.route('/add_students', methods=['POST'])
@login_required
@authorize({'teacher', 'admin'})
@ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
def add_students():
    course_id = request.form['course_id']
    student_usernames = request.form['student_usernames'].split(',')
    students = list(User.objects.raw({'username': {'$in': student_usernames}, 'type': 'student'}))
    if len(students) == len(student_usernames):
        # check if students has already been in this class
        _qs = CourseToStudent.objects.raw({
            'course_id': ObjectId(course_id),
            'student_id': {'$in': [student._id for student in students]}
        })
        if _qs.count() != 0:
            return jsonify({
                'success': 0,
                'msg': error_msg.STUDENT_ALREADY_IN_CLASS
            }), 409
        try:
            CourseToStudent.objects.bulk_create([
                CourseToStudent(course_id, student._id) for student in students
            ])
            return jsonify({
                'success': 1
            })
        except ValidationError as e:
            logger.warning(
                'Failed to add students. Exception: {}'.format(e.message))
            return jsonify({
                'success': 0,
                'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
            }), 400
    else:
        return jsonify({
            'success': 0,
            'msg': error_msg.ILLEGAL_ARGUMENT
        }), 400


@course.route('/add_teachers', methods=['POST'])
@login_required
@authorize({'admin'})
@ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
def add_teachers():
    course_id = request.form['course_id']
    teacher_usernames = request.form['teacher_usernames'].split(',')
    teachers = list(User.objects.raw({'username': {'$in': teacher_usernames}, 'type': 'teacher'}))
    if len(teachers) == len(teacher_usernames):
        # check if teachers has already been in this class
        _qs = CourseToTeacher.objects.raw({
            'course_id': ObjectId(course_id),
            'teacher_id': {'$in': [teacher._id for teacher in teachers]}
        })
        if _qs.count() != 0:
            return jsonify({
                'success': 0,
                'msg': error_msg.TEACHER_ALREADY_IN_CLASS
            }), 409
        try:
            CourseToTeacher.objects.bulk_create([
                CourseToTeacher(course_id, teacher._id) for teacher in teachers
            ])
            return jsonify({
                'success': 1
            })
        except ValidationError as e:
            logger.warning(
                'Failed to create add teachers. Exception: {}'.format(e.message))
            return jsonify({
                'success': 0,
                'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
            }), 400
    else:
        return jsonify({
            'success': 0,
            'msg': error_msg.ILLEGAL_ARGUMENT
        }), 400


@course.route('/get_all_students', methods=['GET'])
@login_required
@authorize({'teacher', 'admin'})
@ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
def get_all_students():
    course_id = request.args.get('course_id')
    qs = CourseToStudent.objects.raw({'course_id': ObjectId(course_id)})
    res = []
    for each in qs:
        _tmp = filter_public_fields(each.student_id)
        res.append(_tmp)
    return jsonify({
        'success': 1,
        'users': sorted(res, key=lambda x: x['create_at'])
    })


@course.route('/get_all_teachers', methods=['GET'])
@login_required
@authorize({'teacher', 'admin'})
@ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
def get_all_teachers():
    course_id = request.args.get('course_id')
    qs = CourseToTeacher.objects.raw({'course_id': ObjectId(course_id)})
    res = []
    for each in qs:
        _tmp = filter_public_fields(each.teacher_id)
        res.append(_tmp)
    return jsonify({
        'success': 1,
        'users': sorted(res, key=lambda x: x['create_at'])
    })


@course.route('/delete_students', methods=['POST'])
@login_required
@authorize({'teacher', 'admin'})
@ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
def delete_students():
    course_id = request.form['course_id']
    student_usernames = request.form['student_usernames'].split(',')
    students = list(User.objects.raw({'username': {'$in': student_usernames}, 'type': 'student'}))
    if len(students) == len(student_usernames):
        qs = CourseToStudent.objects.raw({
            'student_id': {'$in': [student._id for student in students]},
            'course_id': ObjectId(course_id)
        })
        qs.delete()
        return jsonify({
            'success': 1
        })
    else:
        return jsonify({
            'success': 0,
            'msg': error_msg.ILLEGAL_ARGUMENT
        }), 400


@course.route('/delete_teachers', methods=['POST'])
@login_required
@authorize({'admin'})
@ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
def delete_teachers():
    course_id = request.form['course_id']
    teacher_usernames = request.form['teacher_usernames'].split(',')
    teachers = list(User.objects.raw({'username': {'$in': teacher_usernames}, 'type': 'teacher'}))
    if len(teachers) == len(teacher_usernames):
        qs = CourseToTeacher.objects.raw({
            'teacher_id': {'$in': [teacher._id for teacher in teachers]},
            'course_id': ObjectId(course_id)
        })
        qs.delete()
        return jsonify({
            'success': 1
        })
    else:
        return jsonify({
            'success': 0,
            'msg': error_msg.ILLEGAL_ARGUMENT
        }), 400


@course.route('/search', methods=['GET'])
@login_required
@authorize({'student', 'teacher', 'admin'})
def search():
    user = get_current_user()
    student_id = request.args.get('student_id', None)
    teacher_id = request.args.get('teacher_id', None)
    _query = {}
    if user.type == 'admin':
        if student_id and teacher_id or not student_id and not teacher_id:
            return jsonify({
                'success': 0,
                'msg': error_msg.ILLEGAL_ARGUMENT
            }), 400
        else:
            if student_id:
                _query['type'] = 'student'
            else:
                _query['type'] = 'teacher'
    else:
        if request.args.get('student_id', None) or request.args.get('teacher_id', None):
            return jsonify({
                'success': 0,
                'msg': error_msg.REQUEST_FORBIDDEN
            }), 403
        if user.type == 'student':
            _query['type'] = 'student'
        else:
            _query['type'] = 'teacher'
    if _query['type'] == 'student':
        qs = CourseToStudent.objects.raw({'student_id': user._id})
    else:
        qs = CourseToTeacher.objects.raw({'teacher_id': user._id})
    return jsonify({
        'success': 1,
        'courses': sorted([
            {
                'course_id': str(each.course_id._id),
                'course_name': each.course_id.course_name,
                'create_at': str(each.course_id.create_at)
            } for each in qs], key=lambda x: x['create_at']
        )
    })
