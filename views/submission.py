from datetime import datetime
import json
import logging
import mimetypes

from bson import ObjectId
from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required
from pymodm.context_managers import no_auto_dereference
from pymodm.errors import ValidationError

from db.models import Course, Homework, Submission, SubmissionFile, SubmissionMark
from utils import error_msg, login_utils, utils, view_utils
from views.user import filter_public_fields as filter_user_fields
from views.homework import filter_public_fields as filter_homework_fields

submission_blueprint = Blueprint('submission', __name__)
logger = logging.getLogger(__name__)


# utils

FILE_TYPES = {'audio', 'video', 'image'}


# decorators

pass


# view handlers

@submission_blueprint.route('/submit', methods=['POST'])
@login_required
@login_utils.authorize({'student'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
@view_utils.ensure_exists(Homework, 'homework_id', '_id', error_msg.HOMEWORK_NOT_EXISTS, ObjectId)
def submit():
    user = login_utils.get_current_user()
    course_id = request.form['course_id']
    homework_id = request.form['homework_id']
    content = json.loads(request.form['content'])

    # check if the user has already submitted
    old_submission = Submission.objects.raw({
        'user_id': user._id,
        'course_id': ObjectId(course_id),
        'homework_id': ObjectId(homework_id)
    })
    if old_submission.count() != 0:
        return jsonify({
            'success': 0,
            'msg': error_msg.DUPLICATE_SUBMISSION
        }), 409

    t = datetime.utcnow()
    hw = Homework.objects.get({'_id': ObjectId(homework_id)})
    new_submission = Submission(
        user_id=user._id,
        course_id=course_id,
        homework_id=homework_id,
        after_deadline=t>hw.deadline
    )

    sbm_content = []
    saved_files = []
    # structure of content: multiline, one line of format, and one/two lines of content
    # text
    # {some text content}
    # audio, or some other file types
    # {name of this file}
    # {id of this file in SubmissionFile}
    # ...
    try:
        for c in content:
            sbm_content.append(c['type'])
            if c['type'] not in FILE_TYPES:
                sbm_content.append(c['content'])
            else:
                sbm_content.append(c['file_name'])
                new_file = SubmissionFile(
                    user_id=user._id,
                    course_id=course_id,
                    homework_id=homework_id,
                    file_name=c['file_name'],
                    file_type=c['type'],
                    file_id=request.files[c['file_name']]
                )
                new_file.save()
                saved_files.append(new_file)
                sbm_content.append(str(new_file._id))
        new_submission.content = sbm_content
        new_submission.save()
    except ValidationError as e:
        # delete all saved files in this submission
        for f in saved_files:
            f.delete()

        logger.warning(
            'Failed to create new submission. Exception: {}'.format(e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400

    return jsonify({
        'success': 1,
        'submission_id': str(new_submission._id)
    })


@submission_blueprint.route('/get_students', methods=['GET'])
@login_required
@login_utils.authorize({'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
@view_utils.ensure_exists(Homework, 'homework_id', '_id', error_msg.HOMEWORK_NOT_EXISTS, ObjectId)
def get_students():
    submission = Submission.objects.raw(
        {'homework_id': ObjectId(request.args.get('homework_id'))})

    submissions = []
    for sbm in submission:
        submissions.append({
            'submission_id': str(sbm._id),
            'student_info': filter_user_fields(sbm.user_id),
            'after_deadline': sbm.after_deadline,
            'is_marked': sbm.is_marked,
            'create_at': utils.get_timestamp(sbm.create_at)
        })

    return jsonify({
        'success': 1,
        'submissions': sorted(submissions, key=lambda x: x['create_at'])
    })


@submission_blueprint.route('/get_self', methods=['GET'])
@login_required
@login_utils.authorize({'student'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
def get_self():
    user = login_utils.get_current_user()
    submission = Submission.objects.raw({
        'course_id': ObjectId(request.args.get('course_id')),
        'user_id': user._id
    })

    submissions = []
    for sbm in submission:
        submissions.append({
            'submission_id': str(sbm._id),
            'after_deadline': sbm.after_deadline,
            'is_marked': sbm.is_marked,
            'homework': filter_homework_fields(sbm.homework_id),
            'create_at': utils.get_timestamp(sbm.create_at)
        })

    return jsonify({
        'success': 1,
        'submissions': sorted(submissions, key=lambda x: x['create_at'])
    })


@submission_blueprint.route('/get', methods=['GET'])
@login_required
@login_utils.authorize({'student', 'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
@view_utils.ensure_exists(Homework, 'homework_id', '_id', error_msg.HOMEWORK_NOT_EXISTS, ObjectId)
@view_utils.ensure_exists(Submission, 'submission_id', '_id', error_msg.SUBMISSION_NOT_EXISTS, ObjectId)
def get():
    submission = Submission.objects.get({'_id': ObjectId(request.args.get('submission_id'))})
    user = login_utils.get_current_user()
    if user.type == 'student':
        with no_auto_dereference(Submission):
            if submission.user_id != user._id:
                return jsonify({
                    'success': 0,
                    'msg': error_msg.REQUEST_FORBIDDEN
                }), 403

    content = submission.content
    sbm = []
    i = 0
    n = len(content)
    while i < n:
        ctnt = {}
        ctnt['type'] = content[i]
        i += 1
        if ctnt['type'] not in FILE_TYPES:
            ctnt['content'] = content[i]
        else:
            filename = content[i]
            i += 1
            ctnt['file_id'] = content[i]
        sbm.append(ctnt)
        i += 1

    return jsonify({
        'success': 1,
        'content': sbm,
        'after_deadline': submission.after_deadline,
        'is_marked': submission.is_marked
    })


@submission_blueprint.route('/get_file', methods=['GET'])
@login_required
@login_utils.authorize({'student', 'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
@view_utils.ensure_exists(Homework, 'homework_id', '_id', error_msg.HOMEWORK_NOT_EXISTS, ObjectId)
@view_utils.ensure_exists(Submission, 'submission_id', '_id', error_msg.SUBMISSION_NOT_EXISTS, ObjectId)
@view_utils.ensure_exists(SubmissionFile, 'file_id', '_id', error_msg.SUBMISSIONFILE_NOT_EXISTS, ObjectId)
def get_file():
    sbm_file = SubmissionFile.objects.get({'_id': ObjectId(request.args.get('file_id'))})
    user = login_utils.get_current_user()
    if user.type == 'student':
        with no_auto_dereference(SubmissionFile):
            if sbm_file.user_id != user._id:
                return jsonify({
                    'success': 0,
                    'msg': error_msg.REQUEST_FORBIDDEN
                }), 403

    file = sbm_file.file_id
    return send_file(file, mimetype=mimetypes.guess_type(sbm_file.file_name)[0])


@submission_blueprint.route('/mark', methods=['POST'])
@login_required
@login_utils.authorize({'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
@view_utils.ensure_exists(Homework, 'homework_id', '_id', error_msg.HOMEWORK_NOT_EXISTS, ObjectId)
@view_utils.ensure_exists(Submission, 'submission_id', '_id', error_msg.SUBMISSION_NOT_EXISTS, ObjectId)
def mark():
    user = login_utils.get_current_user()
    course_id = request.form['course_id']
    homework_id = request.form['homework_id']
    submission_id = request.form['submission_id']
    content = request.form['content']
    score = int(request.form['score'])

    # check if the submission has already been marked
    sbm = Submission.objects.get({
        '_id': ObjectId(submission_id)
    })
    if sbm.is_marked == 1:
        return jsonify({
            'success': 0,
            'msg': error_msg.SUBMISSION_ALREADY_MARKED
        }), 409

    try:
        new_mark = SubmissionMark(
            user_id = user._id,
            course_id = course_id,
            homework_id = homework_id,
            submission_id = submission_id,
            content = content,
            score = score
        )
        new_mark.save()
    except ValidationError as e:
        logger.warning(
            'Failed to create new submission mark. Exception: {}'.format(e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400

    sbm.is_marked = 1
    sbm.save()
    return jsonify({
        'success': 1
    })


@submission_blueprint.route('/get_mark', methods=['GET'])
@login_required
@login_utils.authorize({'student', 'teacher'})
@view_utils.ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
@view_utils.ensure_user_in_course
@view_utils.ensure_exists(Homework, 'homework_id', '_id', error_msg.HOMEWORK_NOT_EXISTS, ObjectId)
@view_utils.ensure_exists(Submission, 'submission_id', '_id', error_msg.SUBMISSION_NOT_EXISTS, ObjectId)
def get_mark():
    homework_id = request.args.get('homework_id')
    submission_id = request.args.get('submission_id')
    mark = SubmissionMark.objects.get({
        'submission_id': ObjectId(submission_id)
    })
    # get max, min and avg
    all_marks = SubmissionMark.objects.raw({
        'homework_id': ObjectId(homework_id)
    })
    all_scores = [m.score for m in all_marks]
    return jsonify({
        'success': 1,
        'content': mark.content,
        'score': mark.score,
        'score_highest': max(all_scores),
        'score_lowest': min(all_scores),
        'score_average': sum(all_scores) / len(all_scores)
    })
