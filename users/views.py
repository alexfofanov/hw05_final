from django.shortcuts import render
# позволяет узнать ссылку на URL по его имени, параметр name функции path
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CreationForm

import datetime as dt


class SignUp(CreateView):
    form_class = CreationForm
    success_url = "/auth/login/"
    template_name = "signup.html"


def year(request):
    today_date = dt.datetime.today()
    today_year = today_date.year
    
    return {
        'year': today_year,
    }
