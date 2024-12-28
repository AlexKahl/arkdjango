#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 22 09:22:25 2021
@title: "file title goes here"
@description: "file description"
@details: "file description"
@author: Alex Kahl

"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('login/', views.user_login, name="login"),
    path('login/', auth_views.LoginView.as_view(), name="login"),
    path('logout/', views.user_logout, name="logout"),
    path('password_change/', auth_views.PasswordChangeView.as_view(),
         name="password_change"),
    path('password_change_done/', auth_views.PasswordChangeDoneView.as_view(),
         name="password_change_done"),

]
