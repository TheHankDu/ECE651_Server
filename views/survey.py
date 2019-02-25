from datetime import datetime
import json
import logging

from bson import ObjectId
from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required
from pymodm.context_managers import no_auto_dereference
from pymodm.errors import ValidationError

from db.models import Course, Survey
from db import dbutils
from utils import error_msg, login_utils, utils, view_utils
from views.user import filter_public_fields as filter_user_fields

survey_blueprint = Blueprint('survey', __name__)
logger = logging.getLogger(__name__)


# utils

def filter_public_fields(survey):
    public_fields = [
        '_id',
        'course_id',
        'user_id',
        'title',
        'content',
        'create_at'
    ]
    with no_auto_dereference(Survey):
        survey = dbutils.filter_fields(survey, public_fields)
    survey['survey_id'] = str(survey['_id'])
    del survey['_id']
    survey['course_id'] = str(survey['course_id'])
    survey['created_by'] = str(survey['user_id'])
    del survey['user_id']
    survey['create_at'] = utils.get_timestamp(survey['create_at'])
    return survey


# decorators

pass


# view handlers

@survey_blueprint.route('/create', methods=['POST'])
@login_required
@login_utils.authorize({'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
def create():
    user = login_utils.get_current_user()
    course_id = request.form['course_id']
    title = request.form['title']
    content = request.form['content']

    new_survey = Survey(
        user_id = user._id,
        course_id = course_id,
        title = title,
        content = content
    )
    try:
        new_survey.save()
    except ValidationError as e:
        logger.warning(
            'Failed to create survey. Exception: {}'.format(e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400

    return jsonify({
        'success': 1,
        'survey_id': str(new_survey._id)
    })


@survey_blueprint.route('/get', methods=['GET'])
@login_required
@login_utils.authorize({'student', 'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
@view_utils.ensure_exists(Survey, 'survey_id', '_id', error_msg.SURVEY_NOT_EXISTS, ObjectId)
def get():
    survey = Survey.objects.get({'_id': ObjectId(request.args.get('survey_id'))})

    return jsonify({
        'success': 1,
        'survey': filter_public_fields(survey)
    })


@survey_blueprint.route('/update', methods=['POST'])
@login_required
@login_utils.authorize({'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
@view_utils.ensure_exists(Survey, 'survey_id', '_id', error_msg.SURVEY_NOT_EXISTS, ObjectId)
def update():
    survey_id = request.form['survey_id']
    survey = Survey.objects.get({'_id': ObjectId(survey_id)})
    try:
        survey.title = request.form['title']
        survey.content = request.form['content']
        survey.save()
    except ValidationError as e:
        logger.warning(
            'Failed to update survey {}. Exception: {}'.format(survey_id, e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400

    with no_auto_dereference(Survey):
        logger.info('Updated survey. _id:{}, course_id:{}, title:{}'.format(
            str(survey._id), str(survey.course_id), survey.title))

    return jsonify({
        'success': 1
    })


@survey_blueprint.route('/get_all', methods=['GET'])
@login_required
@login_utils.authorize({'student', 'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
def get_all():
    surveys = Survey.objects.raw({'course_id': ObjectId(request.args.get('course_id'))})

    return jsonify({
        'success': 1,
        'surveys': sorted([filter_public_fields(s) for s in surveys], key=lambda x: x['create_at'])
    })
