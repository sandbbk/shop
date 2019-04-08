from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from shop.extentions import send_mail
from datetime import datetime, timedelta
import pytz
from .models import Key
from django.db import transaction
from shop.exceptions import (RequestMethodError, UserAuthError)
import hashlib
from django.utils import timezone



def auth_login(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(username=username, password=password)
    if user is not None and user.is_active:
        login(request, user)
    return user


def log_in(request):
    if request.method == 'POST' and request.is_ajax():
        user = auth_login(request)
        if not user:
            user.username = None
        return JsonResponse({'response': {'user': user.username}})

    if request.method == "GET":
        form = AuthenticationForm()
        return render(request, 'authentication/login.html', {'form': form})
    else:
        user = auth_login(request)
        if user:
            return redirect('/')
        else:
            return render(request, "authentication/login_incorrect.html")


def log_out(request):
    logout(request)
    if request.method == 'POST' and request.is_ajax():
        return JsonResponse({'response': 'you are logged out'})
    return redirect(request.GET.get('next'))


@transaction.atomic
def register(request):
    if request.method == "GET":
        form = UserCreationForm()
        return render(request, 'authentication/register.html', {'form': form})
    else:
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            key = (hashlib.sha256(user.email.encode('utf-8'))).hexdigest()
            key = Key.objects.create(user=user, data=key, expire_time=(timezone.now() + timedelta(minutes=1)))
            subject = 'Activation of account on GoShop'
            send_mail(user.email, subject, 'authentication/activate.html', key.data)
        ne_xt = request.GET.get('next')
        if ne_xt in ('/register', '/login') or ne_xt is None:
            return redirect('/')
        elif ne_xt:
            return redirect(ne_xt)
        else:
            return


def activate(request, link):
    try:
        if request.method != 'GET':
            raise RequestMethodError('Invalid request method')
        key = Key.objects.get(data=link)
        if key.expire_time <= timezone.now():
            key.user.delete()
            raise UserAuthError('Time for activation expired!')
        key.user.is_active = True
        key.user.save()
        key.delete()
        response = {'response': {'msg': f'{key.user.username} profile activated'}}
    except UserAuthError as e:
        return JsonResponse({'response': {'error': repr(e)}})
    return redirect('/login')

