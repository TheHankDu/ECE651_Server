import pymongo
from pymodm import MongoModel, fields

from utils.config import conf
from utils.utils import get_timestamp


class User(MongoModel):
    username = fields.CharField(required=True, blank=False)
    last_name = fields.CharField(required=True, blank=False)
    first_name = fields.CharField(required=True, blank=False)
    full_name = fields.CharField(required=True, blank=False)
    password = fields.CharField(required=True, blank=False)
    email = fields.EmailField(required=True)
    birthday = fields.DateTimeField(required=True)
    type = fields.CharField(required=True, blank=False, choices=['admin', 'student', 'teacher'])
    create_at = fields.DateTimeField(required=True, default=get_timestamp)

    class Meta:
        indexes = [
            pymongo.IndexModel([('username', pymongo.ASCENDING)]),
            pymongo.IndexModel([('email', pymongo.ASCENDING)])
        ]


class Course(MongoModel):
    course_name = fields.CharField(required=True, blank=False)
    create_at = fields.DateTimeField(required=True, default=get_timestamp)

    class Meta:
        indexes = [pymongo.IndexModel([('course_name', pymongo.ASCENDING)])]


class CourseToStudent(MongoModel):
    course_id = fields.ReferenceField(Course, required=True)
    student_id = fields.ReferenceField(User, required=True)
    create_at = fields.DateTimeField(required=True, default=get_timestamp)

    class Meta:
        indexes = [pymongo.IndexModel([('course_id', pymongo.ASCENDING)]),
                   pymongo.IndexModel([('student_id', pymongo.ASCENDING)])]


class CourseToTeacher(MongoModel):
    course_id = fields.ReferenceField(Course, required=True)
    teacher_id = fields.ReferenceField(User, required=True)
    create_at = fields.DateTimeField(required=True, default=get_timestamp)

    class Meta:
        indexes = [pymongo.IndexModel([('course_id', pymongo.ASCENDING)]),
                   pymongo.IndexModel([('teacher_id', pymongo.ASCENDING)])]


class Slides(MongoModel):
    title = fields.CharField(required=True, blank=False)
    content = fields.CharField(required=True, blank=False)
    course_id = fields.ReferenceField(Course, required=True)
    author = fields.ReferenceField(User, required=True)
    create_at = fields.DateTimeField(required=True, default=get_timestamp)

    class Meta:
        indexes = [pymongo.IndexModel([('title', pymongo.ASCENDING)]),
                   pymongo.IndexModel([('course_id', pymongo.ASCENDING)])]


class Homework(MongoModel):
    course_id = fields.ReferenceField(Course, required=True)
    title = fields.CharField(required=True, blank=False)
    content = fields.CharField(required=True, blank=False)
    deadline = fields.DateTimeField(required=True)
    create_at = fields.DateTimeField(required=True, default=get_timestamp)

    class Meta:
        indexes = [pymongo.IndexModel([('course_id', pymongo.ASCENDING)])]


class Submission(MongoModel):
    user_id = fields.ReferenceField(User, required=True)
    course_id = fields.ReferenceField(Course, required=True)
    homework_id = fields.ReferenceField(Homework, required=True)
    content = fields.ListField(field=fields.CharField(blank=True), blank=True, default=[])
    after_deadline = fields.IntegerField(required=True)
    is_marked = fields.IntegerField(default=0)
    create_at = fields.DateTimeField(required=True, default=get_timestamp)

    class Meta:
        indexes = [
            pymongo.IndexModel([('course_id', pymongo.ASCENDING)]),
            pymongo.IndexModel([('homework_id', pymongo.ASCENDING)])
        ]


class SubmissionFile(MongoModel):
    user_id = fields.ReferenceField(User, required=True)
    course_id = fields.ReferenceField(Course, required=True)
    homework_id = fields.ReferenceField(Homework, required=True)
    file_name = fields.CharField(required=True, blank=True, default='')
    file_type = fields.CharField(required=True, blank=True, default='')
    file_id = fields.FileField(required=True)
    create_at = fields.DateTimeField(required=True, default=get_timestamp)

    class Meta:
        indexes = [
            pymongo.IndexModel([('course_id', pymongo.ASCENDING)]),
            pymongo.IndexModel([('homework_id', pymongo.ASCENDING)])
        ]


class SubmissionMark(MongoModel):
    user_id = fields.ReferenceField(User, required=True)
    course_id = fields.ReferenceField(Course, required=True)
    homework_id = fields.ReferenceField(Homework, required=True)
    submission_id = fields.ReferenceField(Submission, required=True)
    content = fields.CharField(required=True, blank=True, default='')
    score = fields.IntegerField(required=True)
    create_at = fields.DateTimeField(required=True, default=get_timestamp)

    class Meta:
        indexes = [
            pymongo.IndexModel([('course_id', pymongo.ASCENDING)]),
            pymongo.IndexModel([('homework_id', pymongo.ASCENDING)]),
            pymongo.IndexModel([('submission_id', pymongo.ASCENDING)])
        ]


class Announcement(MongoModel):
    user_id = fields.ReferenceField(User, required=True)
    course_id = fields.ReferenceField(Course, required=True)
    title = fields.CharField(required=True, blank=False)
    content = fields.CharField(required=True, blank=False)
    create_at = fields.DateTimeField(required=True, default=get_timestamp)

    class Meta:
        indexes = [
            pymongo.IndexModel([('user_id', pymongo.ASCENDING)]),
            pymongo.IndexModel([('course_id', pymongo.ASCENDING)])
        ]


class Survey(MongoModel):
    user_id = fields.ReferenceField(User, required=True)
    course_id = fields.ReferenceField(Course, required=True)
    title = fields.CharField(required=True, default='')
    content = fields.CharField(required=True, default='')
    create_at = fields.DateTimeField(required=True, default=get_timestamp)

    class Meta:
        indexes = [
            pymongo.IndexModel([('user_id', pymongo.ASCENDING)]),
            pymongo.IndexModel([('course_id', pymongo.ASCENDING)])
        ]


class SurveyResponse(MongoModel):
    user_id = fields.ReferenceField(User, required=True)
    course_id = fields.ReferenceField(Course, required=True)
    survey_id = fields.ReferenceField(Survey, required=True)
    content = fields.CharField(required=True, default='')
    create_at = fields.DateTimeField(required=True, default=get_timestamp)

    class Meta:
        indexes = [
            pymongo.IndexModel([('user_id', pymongo.ASCENDING)]),
            pymongo.IndexModel([('course_id', pymongo.ASCENDING)]),
            pymongo.IndexModel([('survey_id', pymongo.ASCENDING)])
        ]

class Checkin(MongoModel):
    title = fields.CharField(required=True, blank=False)
    course_id = fields.ReferenceField(Course, required=True)
    create_at = fields.DateTimeField(required=True, default=get_timestamp)

    class Meta:
        indexes = [
            pymongo.IndexModel([('course_id', pymongo.ASCENDING)]),
        ]

class CheckinToStudent(MongoModel):
    student_id = fields.ReferenceField(User, required=True)
    checkin_id = fields.ReferenceField(Checkin, required=True)
    status = fields.BooleanField()
    create_at = fields.DateTimeField(required=True, default=get_timestamp)

    class Meta:
        indexes = [
            pymongo.IndexModel([('student_id', pymongo.ASCENDING)]),
            pymongo.IndexModel([('checkin_id', pymongo.ASCENDING)]),
        ]

class VerificationCode(MongoModel):
    user_id = fields.ReferenceField(User, required=True)
    code = fields.CharField(required=True)
    create_at = fields.DateTimeField(required=True, default=get_timestamp)

    class Meta:
        indexes = [
            pymongo.IndexModel([('user_id', pymongo.ASCENDING)]),
            pymongo.IndexModel([('create_at', pymongo.ASCENDING)], expireAfterSeconds=conf['verification_code_ttl_seconds'])
        ]
