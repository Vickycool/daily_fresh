from django.conf import settings
from django.core.mail import send_mail
from celery import Celery

import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "daily_fresh.settings")
django.setup()

app = Celery('celery_task.tasks', broker='redis://127.0.0.1:6379/8')


@app.task
def send_register_active_email(username, email, token):
    subject = '天天生鲜欢迎您'
    '''
    massage = f'<h1>{username},' \
              f'欢迎来到每日优鲜<h1>请点击下面链接激活<br/><' \
              f'a href="http://127.0.0.1:8000/user/active/{token}">' \
              f'http://127.0.0.1:8000/user/active/{token}</a>'
    '''
    massage = ''
    sender = settings.EMAIL_FROM
    receiver = [email]
    html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://127.0.0.1:8000' \
                   '/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (username, token, token)
    send_mail(subject, massage, sender, receiver, html_message=html_message)
