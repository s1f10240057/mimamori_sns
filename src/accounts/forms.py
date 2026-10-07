from django.contrib.auth.forms import UserCreationForm, AuthenticationForm # 追加

from .models import User


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "account_id",
            "email",
            "name",
        )
        labels = {
            "account_id" : "アカウントID",
            "email" : "メールアドレス",
            "name" : "名前",
        }

class LoginFrom(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "アカウントID"