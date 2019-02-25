import logging

from bson import ObjectId
from flask import Blueprint, request, jsonify
from flask_login import login_required
from pymodm.errors import ValidationError

from db.models import Course, Slides
from utils import error_msg
from utils.login_utils import authorize
from utils.login_utils import get_current_user
from utils.utils import get_timestamp
from utils.view_utils import ensure_exists

slides = Blueprint('course/slides', __name__)
logger = logging.getLogger(__name__)


@slides.route('/create', methods=['POST'])
@login_required
@authorize({'teacher', 'admin'})
@ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
def create():
    """teachers or administrators create a slide for a course, all the students in this course can see it."""
    try:
        slides = Slides(
            author=get_current_user()._id,
            title=request.form['title'],
            content=request.form['content'],
            course_id=ObjectId(request.form['course_id'])
        )
        slides.save()
        return jsonify({
            'success': 1,
            'slides_id': str(slides._id)
        })
    except ValidationError as e:
        logger.warning(
            'Failed to create new slides. Exception: {}'.format(e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400


@slides.route('/list', methods=['GET'])
@login_required
@authorize({'admin', 'teacher', 'admin'})
@ensure_exists(Course, 'course_id', '_id', error_msg.COURSE_NOT_EXISTS, ObjectId)
def list():
    """show all the slides for a specific class"""
    course_id = request.args.get('course_id')
    qs = Slides.objects.raw({'course_id': ObjectId(course_id)})
    return jsonify({
        'success': 1,
        'slides': sorted(
            [{
                'author': str(each.author._id),
                'title': each.title,
                'content': each.content,
                'slides_id': str(each._id),
                'create_at': get_timestamp(each.create_at)
            } for each in qs], key=lambda x: x['create_at']
        )
    })


@slides.route('/update', methods=['POST'])
@login_required
@authorize({'teacher', 'admin'})
@ensure_exists(Slides, 'slides_id', '_id', error_msg.SLIDES_NOT_EXISTS, ObjectId)
def update():
    slides_id = request.form['slides_id']
    slides = Slides.objects.get({'_id': ObjectId(slides_id)})
    slides.title = request.form['title']
    slides.content = request.form['content']
    slides.save()
    return jsonify({
        'success': 1
    })


@slides.route('/delete', methods=['POST'])
@login_required
@authorize({'teacher', 'admin'})
@ensure_exists(Slides, 'slides_id', '_id', error_msg.SLIDES_NOT_EXISTS, ObjectId)
def delete():
    slides_id = request.form['slides_id']
    slides = Slides.objects.get({'_id': ObjectId(slides_id)})
    slides.delete()
    return jsonify({
        'success': 1
    })


@slides.route('/get', methods=['GET'])
@login_required
@authorize({'student', 'teacher', 'admin'})
@ensure_exists(Slides, 'slides_id', '_id', error_msg.SLIDES_NOT_EXISTS, ObjectId)
def get():
    slides_id = request.args.get('slides_id')
    slides = Slides.objects.get({'_id': ObjectId(slides_id)})
    return jsonify({
        'success': 1,
        'slides': {
            'author': str(slides.author._id),
            'title': slides.title,
            'content': slides.content
        }
    })
