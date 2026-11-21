from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from accounts.models import User

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('name', 'account_id', 'email')
        labels = {
            'name': '名前',
            'account_id': 'アカウントID',
            'email': 'メールアドレス',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '名前を入力してください'}),
            'account_id': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '10', 'placeholder': '半角英数字（最大10文字）'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'メールアドレスを入力してください'}),
        }
        help_texts = {
            'account_id': '※ ログイン時に使用するIDです（最大10文字）。変更すると次回からのログインIDも変更されます。',
        }

    def clean_account_id(self):
        account_id = self.cleaned_data.get('account_id')
        if User.objects.exclude(pk=self.instance.pk).filter(account_id=account_id).exists():
            raise forms.ValidationError("このアカウントIDは既に使用されています。")
        return account_id

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("このメールアドレスは既に使用されています。")
        return email


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
