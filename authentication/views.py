from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from shop.extentions import send_email
from datetime import datetime, timedelta
from .models import Key


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
            key = f'{user.name} + {str(datetime.now())}'
            key = Key.objects.create(user=user, data=key, expire_time=(datetime.now() + timedelta(hours=12)))
            subject = 'Activation of account on GoShop'
            send_email(user.email, subject, 'authentication/activate.html', )

        next = request.GET.get('next')
        if next in ('/register', '/login') or next is None:
            return redirect('/')
        elif next:
            return redirect(next)


def activate(request):
    pass
