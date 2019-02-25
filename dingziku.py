import logging
import sys

from app import app
from db import dbutils
from utils import config


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('args: config_file')
        exit(0)

    config.initialize(sys.argv[1])
    dbutils.connect_db(config.conf['database_uri'])

    host = config.conf['host']
    port = config.conf['port']
    logging.info('Server listening on {}:{}'.format(host, port))
    import views
    app.run(threaded=True, host=host, port=port)
