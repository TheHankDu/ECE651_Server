from . import error_handlers

from .user import user_blueprint
from .auth import auth_blueprint
from .course import course
from .homework import homework_blueprint
from .announcement import announcement_blueprint
from .submission import submission_blueprint
from .survey import survey_blueprint
from .survey_response import survey_response_blueprint
from .slides import slides
from .checkin import checkin
from app import app



app.register_blueprint(blueprint=user_blueprint, url_prefix='/user')
app.register_blueprint(blueprint=auth_blueprint, url_prefix='/auth')
# register blueprint for view/course.py
app.register_blueprint(blueprint=course, url_prefix='/course')
app.register_blueprint(blueprint=homework_blueprint, url_prefix='/course/homework')
app.register_blueprint(blueprint=announcement_blueprint, url_prefix='/course/announcement')
app.register_blueprint(blueprint=submission_blueprint, url_prefix='/course/homework/submission')
app.register_blueprint(blueprint=survey_blueprint, url_prefix='/course/survey')
app.register_blueprint(blueprint=survey_response_blueprint, url_prefix='/course/survey/response')
app.register_blueprint(blueprint=slides, url_prefix='/course/slides')
app.register_blueprint(blueprint=checkin, url_prefix='/course/checkin')
