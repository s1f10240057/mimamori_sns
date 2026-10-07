from django.contrib.auth import login, authenticate
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.views import LoginView as BaseLoginView,  LogoutView as BaseLogoutView
from django.urls import reverse_lazy
from .forms import SignUpForm, LoginFrom
# from mimamori_service import create_dummy_readings
from .models import User
import random


# class IndexView(TemplateView):
#     template_name = "index.html"


class SignupView(CreateView):
    form_class = SignUpForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("mimamori:index")

    def form_valid(self, form):
        # login after signup
        response = super().form_valid(form)
        user = self.object
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')

        return response


class LoginView(BaseLoginView):
    form_class = LoginFrom
    template_name = "accounts/login.html"

class LogoutView(BaseLogoutView):
    success_url = reverse_lazy("mimamori:index")