import datetime as dt

from django.views.generic import CreateView

from .forms import CreationForm


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
