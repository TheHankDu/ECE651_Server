import json
import logging

from bson import ObjectId
from flask import Blueprint, request, jsonify
from flask_login import login_required
from pymodm.context_managers import no_auto_dereference
from pymodm.errors import ValidationError

from db.models import Checkin, CheckinToStudent, Course
from utils import error_msg
from utils.login_utils import authorize
from utils.view_utils import ensure_exists
from utils.utils import get_timestamp

checkin = Blueprint('course/checkin', __name__)
logger = logging.getLogger(__name__)


@checkin.route('/create', methods=['POST'])
@login_required
@authorize({'teacher', 'admin'})
@ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
def create():
    content = json.loads(request.form['content'])
    try:
        c = Checkin(title=request.form['title'], course_id=request.form['course_id'])
        c.save()
        CheckinToStudent.objects.bulk_create([
            CheckinToStudent(
                student_id=student_id,
                checkin_id=c._id,
                status=status
            ) for student_id, status in content.items()
        ])
        return jsonify({
            'success': 1,
            'checkin_id': str(c._id)
        })
    except ValidationError as v:
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(v.message.keys())))
        })


@checkin.route('/update', methods=['POST'])
@login_required
@authorize({'teacher', 'admin'})
@ensure_exists(Checkin, 'checkin_id', '_id', error_msg.CHECKIN_FORM_NOT_EXISTS, ObjectId)
def update():
    new_content = json.loads(request.form['content'])
    checkin_id = request.form['checkin_id']
    with no_auto_dereference(CheckinToStudent):
        qs = CheckinToStudent.objects.raw({'checkin_id': ObjectId(checkin_id),
                                           'student_id': {'$in': [ObjectId(i) for i in new_content.keys()]}
                                           })
        for each in qs:
            each.status = new_content[str(each.student_id)]
            del new_content[str(each.student_id)]
            each.save()
    if len(new_content):
        try:
            CheckinToStudent.objects.bulk_create([
                CheckinToStudent(
                    student_id=ObjectId(student_id),
                    checkin_id=ObjectId(checkin_id),
                    status=status
                ) for student_id, status in new_content.items()
            ])
        except ValidationError as v:
            return jsonify({
                'success': 0,
                'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(v.message.keys())))
            })
    return jsonify({
        'success': 1,
    })


@checkin.route('/list', methods=['GET'])
@login_required
@authorize({'teacher', 'admin'})
@ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
def list():
    course_id = request.args.get('course_id')
    qs = Checkin.objects.raw({'course_id': ObjectId(course_id)})
    return jsonify({
        'success': 1,
        'info': sorted(
            [{
                'title': each.title,
                'checkin_id': str(each._id),
                'create_at': get_timestamp(each.create_at)
            } for each in qs], key=lambda x: x['create_at']
        )
    })


@checkin.route('/get', methods=['GET'])
@login_required
@authorize({'teacher', 'admin'})
@ensure_exists(Checkin, 'checkin_id', '_id', error_msg.CHECKIN_FORM_NOT_EXISTS, ObjectId)
def get():
    checkin_id = request.args.get('checkin_id')
    qs = CheckinToStudent.objects.raw({'checkin_id': ObjectId(checkin_id)})
    return jsonify({
        'success': 1,
        'info': {
            'title': qs[0].checkin_id.title,
            'students': [{
                'student_id': str(each.student_id._id),
                'status': each.status,
            } for each in qs],
            'create_at': get_timestamp(qs[0].checkin_id.create_at)
        }
    })
