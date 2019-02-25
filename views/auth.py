import logging
import threading
import time
import datetime

from flask import Blueprint, jsonify, request
from flask_login import login_user
from pymodm.errors import ValidationError

from db.models import User, VerificationCode
from utils import email_utils, error_msg, login_utils, utils
from utils.config import conf


auth_blueprint = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)


# utils

pass


# decorators

pass


# view handlers

@auth_blueprint.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    try:
        user = User.objects.get({'username': username, 'password': password})
    except:
        return jsonify({
            'success': 0,
            'msg': error_msg.WRONG_PASSWORD
        }), 401

    u = login_utils.UserLogin()
    u.id = user._id
    login_user(u)
    return jsonify({
        'success': 1
    })


@auth_blueprint.route('/send_email_verification_code', methods=['POST'])
def send_email_verification_code():
    email = request.form['email']
    try:
        user = User.objects.get({'email': email})
    except:
        return jsonify({
            'success': 0,
            'msg': error_msg.USER_NOT_EXISTS
        }), 404

    # delete previous verification codes for this user
    prev = VerificationCode.objects.raw({'user_id': user._id})
    prev.delete()

    code = utils.random_string(6)
    new_code = VerificationCode(
        user_id = user._id,
        code = code
    )

    try:
        new_code.save()
    except ValidationError as e:
        logger.warning(
            'Failed to create new verification code. Exception: {}'.format(e.message))
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400

    logger.info('Send verification code to {} {}'.format(str(user._id), user.email))
    email_utils.send(
        email,
        '重置密码验证码','验证码是：{}。请在10分钟内使用。'.format(code)
    )

    return jsonify({
        'success': 1
    })


@auth_blueprint.route('/verify_code', methods=['POST'])
def verify_code():
    email = request.form['email']
    code = request.form['verification_code']
    try:
        user = User.objects.get({'email': email})
    except:
        return jsonify({
            'success': 0,
            'msg': error_msg.USER_NOT_EXISTS
        }), 404

    vcode = VerificationCode.objects.raw({'user_id': user._id})
    if vcode.count() == 0 or vcode.first().code != code:
        return jsonify({
            'success': 1,
            'is_verified': 0
        })

    return jsonify({
        'success': 1,
        'is_verified': 1
    })


@auth_blueprint.route('/reset_password', methods=['POST'])
def reset_password():
    email = request.form['email']
    code = request.form['verification_code']
    new_password = request.form['new_password']
    try:
        user = User.objects.get({'email': email})
    except:
        return jsonify({
            'success': 0,
            'msg': error_msg.USER_NOT_EXISTS
        }), 404

    vcode = VerificationCode.objects.raw({'user_id': user._id})
    if vcode.count() == 0 or vcode.first().code != code:
        return jsonify({
            'success': 1,
            'is_verified': 0
        })

    try:
        user.password = new_password
        user.save()
    except ValidationError as e:
        return jsonify({
            'success': 0,
            'msg': '{}: {}'.format(error_msg.ILLEGAL_ARGUMENT, ','.join(list(e.message.keys())))
        }), 400

    # delete the verification code after it's used
    vcode.delete()

    return jsonify({
        'success': 1,
        'is_verified': 1
    })
