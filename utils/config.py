import json
import logging
import os

conf = {
    "log_level": "INFO",
    "host": "0.0.0.0",
    "port": os.environ.get("PORT", 9991),
    "database_uri": "",
    "database_name": "",
    "verification_code_ttl_seconds": 600,
    "smtp_server": "smtp.sendgrid.net",
    "smtp_port": 25,
    "smtp_username": "apikey",
    "smtp_password": "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",
    "email_addr": "dzk_auth@test-email.com"
}

# sendgrid account
# username: dingziku
# password: ohsocool123

# recovery email of sendgrid account -> protonmail.com
# username: dzk_auth
# password: ohsocool


def initialize(config_file):
    with open(config_file) as f:
        conf_in_file = json.load(f)
        for k, v in conf_in_file.items():
            if k in conf:
                conf[k] = v
    log_level = logging.INFO
    if conf['log_level'].upper() == 'DEBUG':
        log_level = logging.DEBUG
    elif conf['log_level'].upper() == 'WARNING':
        log_level = logging.WARNING
    elif conf['log_level'].upper() == 'ERROR':
        log_level = logging.ERROR
    else:
        print('Unknown logging level in config: {}. Will use INFO'.format(conf['log_level']))
        conf['log_level'] = 'INFO'
    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s')
