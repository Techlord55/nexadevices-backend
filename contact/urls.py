
# backend/contact/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.contact_submit, name='contact-submit'),
]