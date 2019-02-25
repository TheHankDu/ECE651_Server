import logging

from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_login import login_required
from pymodm.context_managers import no_auto_dereference
from pymodm.errors import ValidationError

from db import dbutils
from db.models import Homework, Course
from utils import error_msg, login_utils, utils, view_utils

homework_blueprint = Blueprint('homework', __name__)
logger = logging.getLogger(__name__)


# utils

def filter_public_fields(homework):
    public_fields = [
        '_id',
        'course_id',
        'title',
        'content',
        'deadline',
        'create_at'
    ]
    with no_auto_dereference(Homework):
        homework = dbutils.filter_fields(homework, public_fields)
    homework['id'] = str(homework['_id'])
    del homework['_id']
    homework['course_id'] = str(homework['course_id'])
    homework['deadline'] = utils.get_timestamp(homework['deadline'])
    homework['create_at'] = utils.get_timestamp(homework['create_at'])
    return homework


# decorators

pass


# view handlers

@homework_blueprint.route('/create', methods=['POST'])
@login_required
@login_utils.authorize({'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
def create():
    try:
        new_homework = Homework(
            course_id=request.form['course_id'],
            title=request.form['title'],
            content=request.form['content'],
            deadline=utils.parse_timestamp(request.form['deadline'])
        )
        new_homework.save()
    except ValidationError as e:
        logger.warning(
            'Failed to create new homework. Exception: {}'.format(e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400

    logger.info('Created new homework. _id:{}, course_id:{}, title:{}'.format(
        str(new_homework._id), str(new_homework.course_id._id), new_homework.title))

    return jsonify({
        'success': 1,
        'homework_id': str(new_homework._id)
    })


@homework_blueprint.route('/update', methods=['POST'])
@login_required
@login_utils.authorize({'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
@view_utils.ensure_exists(Homework, 'homework_id', '_id', error_msg.HOMEWORK_NOT_EXISTS, ObjectId)
def update():
    homework_id = request.form['homework_id']
    homework = Homework.objects.get({'_id': ObjectId(homework_id)})
    try:
        homework.course_id = request.form['course_id']
        homework.title = request.form['title']
        homework.content = request.form['content']
        homework.deadline = utils.parse_timestamp(request.form['deadline'])
        homework.save()
    except ValidationError as e:
        logger.warning(
            'Failed to update homework {}. Exception: {}'.format(homework_id, e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400

    logger.info('Updated homework. _id:{}, course_id:{}, title:{}'.format(
        str(homework._id), str(homework.course_id._id), homework.title))

    return jsonify({
        'success': 1
    })


@homework_blueprint.route('/get_all', methods=['GET'])
@login_required
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
def get_all():
    homeworks = Homework.objects.raw(
        {'course_id': ObjectId(request.args.get('course_id'))})
    return jsonify({
        'success': 1,
        'homeworks': sorted([
            filter_public_fields(h) for h in homeworks
        ], key=lambda x: x['create_at'])
    })
