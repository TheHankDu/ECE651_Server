from email.header import Header
from email.mime.text import MIMEText
import logging
import smtplib

from utils.config import conf


logger = logging.getLogger(__name__)

def send(to, title, content):
    logger.info('Send email {}:{}'.format(to, title))
    msg = MIMEText(content)
    msg['From'] = Header(conf['email_addr'], 'utf-8)')
    msg['To'] = Header(to, 'utf-8')
    msg['Subject'] = Header(title, 'utf-8')
    s = smtplib.SMTP('{}:{}'.format(conf['smtp_server'], conf['smtp_port']))
    s.login(conf['smtp_username'], conf['smtp_password'])
    s.sendmail(conf['email_addr'], [to], msg.as_string())
    s.quit()
