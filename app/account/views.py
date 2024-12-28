from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from .forms import LoginForm

# Create your views here.


def user_login(request):

    if request.method == "POST":

        form = LoginForm(request.POST)

        if not form.is_valid():
            form = LoginForm()

        else:

            cd = form.cleaned_data
            user = authenticate(request, username=cd["username"], password=cd["password"])

            if user is None:
                return HttpResponse('Invalid login')

            if not user.is_active:
                return HttpResponse('Disabled account')

            login(request, user)
            return redirect("home")
    
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})


def user_logout(request):
    logout(request)

    form = LoginForm()
    return redirect("login")