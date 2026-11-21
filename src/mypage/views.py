from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.views import PasswordChangeView
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from accounts.models import User
from .forms import ProfileUpdateForm, CustomPasswordChangeForm


class ProfileView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = ProfileUpdateForm
    template_name = 'mypage/profile.html'
    success_url = reverse_lazy('mypage:profile')
    success_message = "ユーザー情報を更新しました。"

    def get_object(self, queryset=None):
        return self.request.user


class CustomPasswordChangeView(LoginRequiredMixin, SuccessMessageMixin, PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'mypage/password_change.html'
    success_url = reverse_lazy('mypage:profile')
    success_message = "パスワードを変更しました。"
