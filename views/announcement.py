from datetime import datetime
import json
import logging

from bson import ObjectId
from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required
from pymodm.context_managers import no_auto_dereference
from pymodm.errors import ValidationError

from db.models import Announcement, Course, CourseToTeacher
from db import dbutils
from utils import error_msg, login_utils, utils, view_utils
from views.user import filter_public_fields as filter_user_fields

announcement_blueprint = Blueprint('announcement', __name__)
logger = logging.getLogger(__name__)


# utils

def filter_public_fields(announcement):
    public_fields = [
        '_id',
        'user_id',
        'course_id',
        'title',
        'content',
        'create_at'
    ]
    announcement = dbutils.filter_fields(announcement, public_fields)
    announcement['announcement_id'] = str(announcement['_id'])
    del announcement['_id']
    announcement['teacher_info'] = filter_user_fields(announcement['user_id'])
    del announcement['user_id']
    announcement['course_id'] = str(announcement['course_id']._id)
    announcement['create_at'] = utils.get_timestamp(announcement['create_at'])
    return announcement


# decorators

pass


# view handlers

@announcement_blueprint.route('/create', methods=['POST'])
@login_required
@login_utils.authorize({'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
def create():
    user = login_utils.get_current_user()
    course_id = request.form['course_id']
    title = request.form['title']
    content = request.form['content']

    try:
        new_announcement = Announcement(
            user_id=user._id,
            course_id=course_id,
            title=title,
            content=content
        )
        new_announcement.save()
    except ValidationError as e:
        logger.warning(
            'Failed to create new announcement. Exception: {}'.format(e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400

    return jsonify({
        'success': 1,
        'survey_id': str(new_announcement._id)
    })


@announcement_blueprint.route('/update', methods=['POST'])
@login_required
@login_utils.authorize({'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
@view_utils.ensure_exists(Announcement, 'announcement_id', '_id', error_msg.ANNOUNCEMENT_NOT_EXISTS, ObjectId)
def update():
    announcement_id = request.form['announcement_id']
    announcement = Announcement.objects.get({'_id': ObjectId(announcement_id)})
    try:
        announcement.title = request.form['title']
        announcement.content = request.form['content']
        announcement.save()
    except ValidationError as e:
        logger.warning(
            'Failed to update survey {}. Exception: {}'.format(announcement_id, e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400

    with no_auto_dereference(Announcement):
        logger.info('Updated announcement. _id:{}, course_id:{}'.format(
            str(announcement._id), str(announcement.course_id)))

    return jsonify({
        'success': 1
    })


@announcement_blueprint.route('/get_all', methods=['GET'])
@login_required
@login_utils.authorize({'student', 'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
def get_all():
    announcements = Announcement.objects.raw({'course_id': ObjectId(request.args.get('course_id'))})

    return jsonify({
        'success': 1,
        'announcements': sorted([filter_public_fields(a) for a in announcements], key=lambda x: x['create_at'])
    })


@announcement_blueprint.route('/get', methods=['GET'])
@login_required
@login_utils.authorize({'student', 'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
@view_utils.ensure_exists(Announcement, 'announcement_id', '_id', error_msg.ANNOUNCEMENT_NOT_EXISTS, ObjectId)
def get():
    announcement = Announcement.objects.get(
        {'_id': ObjectId(request.args.get('announcement_id'))})

    return jsonify({
        'success': 1,
        'announcement': filter_public_fields(announcement)
    })

