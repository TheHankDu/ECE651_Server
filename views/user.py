from datetime import date
from functools import wraps
import logging

from flask import Blueprint, jsonify, request
from flask_login import login_required
from pymodm.errors import ValidationError

from db import dbutils
from db.models import User
from utils import error_msg, view_utils, login_utils
from utils.utils import get_timestamp

user_blueprint = Blueprint('user', __name__)
logger = logging.getLogger(__name__)


# utils

def filter_public_fields(user):
    public_fields = [
        '_id',
        'username',
        'last_name',
        'first_name',
        'email',
        'birthday',
        'type',
        'create_at'
    ]
    user = dbutils.filter_fields(user, public_fields)
    user['user_id'] = str(user['_id'])
    del user['_id']
    user['birthday_year'] = user['birthday'].year
    user['birthday_month'] = user['birthday'].month
    user['birthday_day'] = user['birthday'].day
    del user['birthday']
    user['create_at'] = get_timestamp(user['create_at'])
    return user


# decorators

def check_birthday(f):
    @wraps(f)
    def check():
        try:
            birthday = date(int(request.form['birthday_year']),
                            int(request.form['birthday_month']),
                            int(request.form['birthday_day']))
        except ValueError as e:
            logger.warning(
                'Failed to create new user, wrong birthday: {}'.format(e))
            return jsonify({
                'success': 0,
                'msg': '{}: birthday_year,birthday_month,birthday_day'.format(error_msg.ILLEGAL_ARGUMENT)
            }), 400
        return f()
    return check


# view handlers

@user_blueprint.route('/register', methods=['POST'])
@view_utils.ensure_not_exists(User, 'username', 'username', error_msg.DUPLICATE_USERNAME)
@view_utils.ensure_not_exists(User, 'email', 'email', error_msg.DUPLICATE_EMAIL)
@check_birthday
def register():
    birthday = date(int(request.form['birthday_year']),
                    int(request.form['birthday_month']),
                    int(request.form['birthday_day']))

    try:
        username = request.form['username']
        new_user = User(
            username=username,
            last_name=request.form['last_name'],
            first_name=request.form['first_name'],
            full_name=request.form['last_name'] + request.form['first_name'],
            password=request.form['password'],
            email=request.form['email'],
            birthday=birthday,
            type=request.form['type']
        )
        new_user.save()
    except ValidationError as e:
        logger.warning(
            'Failed to create new user. Exception: {}'.format(e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400

    logger.info('Created new user: {}'.format(username))
    return jsonify({'success': 1})


@user_blueprint.route('/get_info', methods=['GET'])
@login_required
@login_utils.authorize({'student', 'teacher'}, {'teacher'})
@view_utils.ensure_exists(User, 'username', 'username', error_msg.USER_NOT_EXISTS)
def get_info():
    username = request.args.get('username')
    user = User.objects.get({'username': username})
    user = filter_public_fields(user)
    return jsonify({
        'success': 1,
        **user
    })


@user_blueprint.route('/update_info', methods=['POST'])
@login_required
@login_utils.authorize({'student', 'teacher'})
@view_utils.ensure_exists(User, 'username', 'username', error_msg.USER_NOT_EXISTS)
@check_birthday
def update_info():
    username = request.form['username']
    birthday = date(int(request.form['birthday_year']),
                    int(request.form['birthday_month']),
                    int(request.form['birthday_day']))

    user = User.objects.get({'username': username})
    user.last_name = request.form['last_name']
    user.first_name = request.form['first_name']
    user.full_name = user.last_name + user.first_name
    user.email = request.form['email']
    user.birthday = birthday
    try:
        user.save()
    except ValidationError as e:
        logger.warning(
            'Failed to update user {}. Exception: {}'.format(str(user._id), e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400

    return jsonify({
        'success': 1
    })


@user_blueprint.route('/update_password', methods=['POST'])
@login_required
@login_utils.authorize({'student', 'teacher'}, {})
@view_utils.ensure_exists(User, 'username', 'username', error_msg.USER_NOT_EXISTS)
def update_password():
    username = request.form['username']
    old_password = request.form['old_password']
    new_password = request.form['new_password']

    user = User.objects.get({'username': username})

    if user.password != old_password:
        return jsonify({
            'success': 0,
            'msg': error_msg.WRONG_PASSWORD
        }), 401

    try:
        user.password = new_password
        user.save()
    except ValidationError as e:
        logger.warning(
            'Failed to update password of {}. Exception: {}'.format(str(user._id), e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: new_password'.format(error_msg.ILLEGAL_ARGUMENT)
        }), 400

    return jsonify({
        'success': 1
    })


@user_blueprint.route('/search', methods=['POST'])
@login_required
@login_utils.authorize({'teacher'}, {'teacher'})
def search():
    conds = ['username', 'email', 'name', 'type']
    q = {k: request.form[k] for k in conds if k in request.form}
    if not q:
        return jsonify({
            'success': 0,
            'msg': error_msg.MISSING_ARGUMENT + ': ' + ','.join(conds)
        }), 400

    # for "name", need to search users whose "fullname" contains "name"
    if 'name' in q:
        q['full_name'] = {'$regex': q['name']}  # a little insecure
        del q['name']

    users = User.objects.raw(q)
    ret = [filter_public_fields(u) for u in users]
    return jsonify({
        'success': 1,
        'users': ret
    })
