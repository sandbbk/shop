from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout




def log_in(request):
    if request.method == "GET":
        form = AuthenticationForm()
        return render(request, 'authentication/login.html', {'form': form})
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return redirect('/')

        else:
            return render(request, "authentication/login_incorrect.html")


def log_out(request):
    logout(request)
    return redirect(request.GET.get('next'))

def register(request):
    if request.method == "GET":
        form = UserCreationForm()
        return render(request, 'authentication/register.html', {'form': form})
    else:
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
        next = request.GET.get('next')
        if next in ('/register', '/login') or next is None:
            return redirect('/')
        elif next:
            return redirect(next)
