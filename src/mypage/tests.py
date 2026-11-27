from django.test import TestCase
from django.urls import reverse
from accounts.models import User

class MyPageTests(TestCase):
    def setUp(self):
        self.user1 = User(
            email='user1@example.com',
            account_id='user1',
            name='ユーザー1',
            role='A'
        )
        self.user1.set_password('Password123!')
        self.user1.save()

        self.user2 = User(
            email='user2@example.com',
            account_id='user2',
            name='ユーザー2',
            role='B'
        )
        self.user2.set_password('Password123!')
        self.user2.save()

    def test_login_required(self):
        # 未ログイン時はログイン画面へリダイレクト
        response = self.client.get(reverse('mypage:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

        response = self.client.get(reverse('mypage:password_change'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_profile_view(self):
        # ログインユーザーのマイページ表示
        self.client.login(username='user1', password='Password123!')
        response = self.client.get(reverse('mypage:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ユーザー1')
        self.assertContains(response, 'user1')
        self.assertContains(response, 'user1@example.com')

    def test_profile_update_success(self):
        # 名前、アカウントID、メールアドレスの正常更新
        self.client.login(username='user1', password='Password123!')
        response = self.client.post(reverse('mypage:profile'), {
            'name': '更新後名前',
            'account_id': 'user1new',
            'email': 'user1new@example.com',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ユーザー情報を更新しました。')

        self.user1.refresh_from_db()
        self.assertEqual(self.user1.name, '更新後名前')
        self.assertEqual(self.user1.account_id, 'user1new')
        self.assertEqual(self.user1.email, 'user1new@example.com')

    def test_profile_update_keep_same_account_id_and_email(self):
        # 自身の既存アカウントIDやメールアドレスを保持したまま名前のみ変更
        self.client.login(username='user1', password='Password123!')
        response = self.client.post(reverse('mypage:profile'), {
            'name': '名前だけ変更',
            'account_id': 'user1',
            'email': 'user1@example.com',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.name, '名前だけ変更')

    def test_profile_update_duplicate_account_id(self):
        # 他人のアカウントIDと重複する場合はエラー
        self.client.login(username='user1', password='Password123!')
        response = self.client.post(reverse('mypage:profile'), {
            'name': 'ユーザー1',
            'account_id': 'user2',  # user2 と重複
            'email': 'user1@example.com',
        })

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('account_id', form.errors)
        self.assertIn('このアカウントIDは既に使用されています。', form.errors['account_id'])
        self.assertContains(response, 'このアカウントIDは既に使用されています。')
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.account_id, 'user1')

    def test_profile_update_duplicate_email(self):
        # 他人のメールアドレスと重複する場合はエラー
        self.client.login(username='user1', password='Password123!')
        response = self.client.post(reverse('mypage:profile'), {
            'name': 'ユーザー1',
            'account_id': 'user1',
            'email': 'user2@example.com',  # user2 と重複
        })

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('email', form.errors)
        self.assertIn('このメールアドレスは既に使用されています。', form.errors['email'])
        self.assertContains(response, 'このメールアドレスは既に使用されています。')
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.email, 'user1@example.com')

    def test_password_change_success(self):
        # パスワード変更成功
        self.client.login(username='user1', password='Password123!')
        response = self.client.post(reverse('mypage:password_change'), {
            'old_password': 'Password123!',
            'new_password1': 'NewPass987!',
            'new_password2': 'NewPass987!',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'パスワードを変更しました。')

        # 新パスワードでログインできること
        self.client.logout()
        login_success = self.client.login(username='user1', password='NewPass987!')
        self.assertTrue(login_success)

    def test_password_change_wrong_old_password(self):
        # 誤った旧パスワード
        self.client.login(username='user1', password='Password123!')
        response = self.client.post(reverse('mypage:password_change'), {
            'old_password': 'WrongPassword!',
            'new_password1': 'NewPass987!',
            'new_password2': 'NewPass987!',
        })

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('old_password', form.errors)
        self.assertContains(response, '元のパスワードが間違っています')
