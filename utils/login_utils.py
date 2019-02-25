from bson import ObjectId
from functools import wraps
import logging

from flask import jsonify, request
import flask_login

from app import app
from db.models import User
from utils import error_msg


logger = logging.getLogger(__name__)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)


class UserLogin(flask_login.UserMixin):
    def __init__(self):
        super().__init__()
        self.user_obj = None


@login_manager.user_loader
def user_loader(user_id):
    try:
        user = User.objects.get({'_id': ObjectId(user_id)})
    except:
        return None

    u = UserLogin()
    u.id = str(user._id)
    u.user_obj = user
    return u


def get_current_user():
    return flask_login.current_user.user_obj


def authorize(user_types=None, types_any_username=None):
    # user_types: types of user that are allowed. leave empty if only admin is allowed
    # types_any_username: types of user who can send requests in which the parameter "username" can be different from their own usernames
    def fail():
        return jsonify({
            'success': 0,
            'msg': error_msg.REQUEST_FORBIDDEN
        }), 403

    def wrapper(f):
        @wraps(f)
        def wrapped():
            nonlocal user_types, types_any_username
            if not user_types:
                user_types = set()
            user_types.add('admin')
            if not types_any_username:
                types_any_username = set()
            types_any_username.add('admin')

            user = get_current_user()
            if user.type not in user_types:
                logger.warn('User with not authorized user type, {}:{}:{}'.format(
                    str(user._id), user.username, user.type))
                return fail()

            if request.method == 'GET':
                username_in_req = request.args.get('username', None)
            else:
                username_in_req = request.form.get('username', None)
            if username_in_req:
                if user.type not in types_any_username and user.username != username_in_req:
                    logger.warn('User with not authorized username in request, {}:{}:{}'.format(
                        str(user._id), user.username, username_in_req))
                    return fail()
            return f()
        return wrapped
    return wrapper
