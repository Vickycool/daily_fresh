from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import authenticate

from itsdangerous import SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import re

from user.models import User
from celery_task.tasks import send_register_active_email


# Create your views here.
# /user/register
def register(request):
    return render(request, 'register.html')

# /user/register/register_handle
def register_handle(request):
    '''
    接收数据
    数据校验
    业务处理
    返回响应
    '''
    if request.method == 'GET':
        return render(request, 'register.html')
    else:
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不能为空'})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱不合法'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': '用户已存在'})

        user = User.objects.create_user(username, email, password)
        user.is_active == 0
        user.save()
        # 跳转到首页
        return redirect(reverse('goods:index'))


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不能为空'})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱不合法'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': '用户已存在'})

        user = User.objects.create_user(username, email, password)
        user.is_active == 0
        user.save()
        '''http://127.0.0.1:8000/user/active/*id'''
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode()
        # 发送注册激活邮件
        send_register_active_email.delay(username, email, token)
        # 跳转到首页
        return redirect(reverse('goods:index'))


class ActiveView(View):
    def get(self, request, token):
        '''进行用户激活'''
        # 进行解密，获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取待激活用户的id
            user_id = info['confirm']

            # 根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')


# user/login
class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        username = request.POST.get('username')
        pwd = request.POST.get('pwd')
        remember = request.POST.get('remember')

        if not all([username, pwd]):
            return render(request, 'login.html', {'errmsg': '用户名或密码不能为空'})

        user = authenticate(username=username, password=pwd)
        if user