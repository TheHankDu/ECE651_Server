from datetime import datetime
import json
import logging

from bson import ObjectId
from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required
from pymodm.context_managers import no_auto_dereference
from pymodm.errors import ValidationError

from db.models import Course, Survey, SurveyResponse
from db import dbutils
from utils import error_msg, login_utils, utils, view_utils
from views.user import filter_public_fields as filter_user_fields

survey_response_blueprint = Blueprint('survey_response', __name__)
logger = logging.getLogger(__name__)


# utils

def filter_public_fields(survey_response):
    public_fields = [
        '_id',
        'user_id',
        'course_id',
        'survey_id',
        'content',
        'create_at'
    ]
    survey_response = dbutils.filter_fields(survey_response, public_fields)
    survey_response['survey_response_id'] = str(survey_response['_id'])
    del survey_response['_id']
    survey_response['student_info'] = filter_user_fields(survey_response['user_id'])
    del survey_response['user_id']
    survey_response['course_id'] = str(survey_response['course_id']._id)
    survey_response['survey_id'] = str(survey_response['survey_id']._id)
    survey_response['create_at'] = utils.get_timestamp(survey_response['create_at'])
    return survey_response


# decorators

pass


# view handlers

@survey_response_blueprint.route('/submit', methods=['POST'])
@login_required
@login_utils.authorize({'student'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
@view_utils.ensure_exists(Survey, 'survey_id', '_id', error_msg.SURVEY_NOT_EXISTS, ObjectId)
def submit():
    user = login_utils.get_current_user()
    course_id = request.form['course_id']
    survey_id = request.form['survey_id']

    # check if already submitted
    old_response = SurveyResponse.objects.raw({
        'course_id': ObjectId(course_id),
        'survey_id': ObjectId(survey_id),
        'user_id': user._id
    })
    if old_response.count() != 0:
        return jsonify({
            'success': 0,
            'msg': error_msg.DUPLICATE_SURVEY_RESPONSE
        }), 409

    content = request.form['content']
    new_response = SurveyResponse(
        user_id = user._id,
        course_id = course_id,
        survey_id = survey_id,
        content = content
    )
    try:
        new_response.save()
    except ValidationError as e:
        logger.warning(
            'Failed to create new survey response. Exception: {}'.format(e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400

    return jsonify({
        'success': 1,
        'survey_response_id': str(new_response._id)
    })


@survey_response_blueprint.route('/update', methods=['POST'])
@login_required
@login_utils.authorize({'student'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
@view_utils.ensure_exists(Survey, 'survey_id', '_id', error_msg.SURVEY_NOT_EXISTS, ObjectId)
@view_utils.ensure_exists(SurveyResponse, 'survey_response_id', '_id', error_msg.SURVEY_RESPONSE_NOT_EXISTS, ObjectId)
def update():
    response_id = request.form['survey_response_id']
    response = SurveyResponse.objects.get({'_id': ObjectId(response_id)})

    user = login_utils.get_current_user()
    with no_auto_dereference(SurveyResponse):
        logger.warn('User {} updating others\'s survey response {}'.format(str(user._id), response_id))
        if user._id != response.user_id:
            return jsonify({
                'success': 0,
                'msg': error_msg.REQUEST_FORBIDDEN
            }), 403

    try:
        response.content = request.form['content']
        response.save()
    except ValidationError as e:
        logger.warning(
            'Failed to update survey response {}. Exception: {}'.format(response_id, e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400

    with no_auto_dereference(Survey):
        logger.info('Updated survey response. _id:{}, course_id:{}'.format(
            str(response._id), str(response.course_id)))

    return jsonify({
        'success': 1
    })


@survey_response_blueprint.route('/get_all', methods=['GET'])
@login_required
@login_utils.authorize({'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
@view_utils.ensure_exists(Survey, 'survey_id', '_id', error_msg.SURVEY_NOT_EXISTS, ObjectId)
def get_all():
    course_id = request.args.get('course_id')
    survey_id = request.args.get('survey_id')
    responses = SurveyResponse.objects.raw({'course_id': ObjectId(course_id), 'survey_id': ObjectId(survey_id)})

    return jsonify({
        'success': 1,
        'surveys': sorted([filter_public_fields(s) for s in responses], key=lambda x: x['create_at'])
    })


@survey_response_blueprint.route('/get', methods=['GET'])
@login_required
@login_utils.authorize({'student', 'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
@view_utils.ensure_exists(Survey, 'survey_id', '_id', error_msg.SURVEY_NOT_EXISTS, ObjectId)
def get():
    user = login_utils.get_current_user()
    course_id = request.args.get('course_id')
    survey_id = request.args.get('survey_id')
    survey_response_id = request.args.get('survey_response_id')
    q = {'course_id': ObjectId(course_id), 'survey_id': ObjectId(survey_id)}
    if user.type == 'student':
        if survey_response_id:
            return jsonify({
                'success': 0,
                'msg': error_msg.REQUEST_FORBIDDEN
            }), 403
        q['user_id'] = user._id
    else:
        q['_id'] = ObjectId(survey_response_id)
    try:
        response = SurveyResponse.objects.get(q)
    except Exception as e:
        return jsonify({
            'success': 0,
            'msg': error_msg.SURVEY_RESPONSE_NOT_EXISTS
        }), 404

    return jsonify({
        'success': 1,
        'response': filter_public_fields(response)
    })
