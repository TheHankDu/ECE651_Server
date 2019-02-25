import logging

from pymodm.connection import connect


logger = logging.getLogger(__name__)


def connect_db(uri, db_name=''):
    try:
        logger.debug('DB uri: {}, database name: {}'.format(uri, db_name))
        connect(uri)
        logger.info('Connected to database')
    except Exception as e:
        logger.exception(
            'Failed to connect to database. Exception: {}'.format(e))
        raise e


def exists(model, query):
    res = model.objects.raw(query)
    return res.count() != 0


def filter_fields(obj, fields):
    return {f: getattr(obj, f) for f in fields}
