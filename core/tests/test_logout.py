"""T006：退出当前会话，允许同一浏览器重新验证另一个账号。"""

from urllib.parse import urlencode, urlsplit

from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.sessions.models import Session
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.tests.test_forms import FormElements


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class LogoutFlowTests(TestCase):
    password = "disposable-logout-test-password"

    @classmethod
    def setUpTestData(cls):
        cls.user_a = get_user_model().objects.create_user("learner_a", password=cls.password)
        cls.user_b = get_user_model().objects.create_user("learner_b", password=cls.password)

    def setUp(self):
        self.login_url = reverse("core:login")
        self.logout_url = reverse("core:logout")
        self.workspace_url = reverse("core:workspace")
        self.home_url = reverse("core:home")

    def login(self, client=None, username="learner_a"):
        return (client or self.client).post(self.login_url, {"username": username, "password": self.password})

    def assert_requires_login(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlsplit(response.headers["Location"]).path, self.login_url)

    def test_authenticated_pages_show_real_post_logout_form(self):
        self.assertNotContains(self.client.get(self.home_url), "退出登录")
        self.login()
        for url in (self.workspace_url, self.home_url):
            response = self.client.get(url)
            self.assertContains(response, "退出登录")
            elements = FormElements(response.content.decode())
            self.assertIn({"class": "nav-logout-form", "method": "post", "action": self.logout_url}, elements.forms)
            self.assertTrue(elements.inputs["csrfmiddlewaretoken"]["value"])

    def test_post_logout_clears_cookie_and_deletes_server_session(self):
        self.login()
        old_key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        response = self.client.post(self.logout_url)
        self.assertRedirects(response, self.home_url)
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertFalse(Session.objects.filter(session_key=old_key).exists())
        cookie = response.cookies[settings.SESSION_COOKIE_NAME]
        self.assertEqual(cookie.value, "")
        self.assertEqual(cookie["max-age"], 0)
        self.assert_requires_login(self.client.get(self.workspace_url))

    def test_old_cookie_replay_is_denied_and_independent_session_survives(self):
        self.login()
        old_cookie = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        independent = Client()
        self.login(independent, "learner_b")
        self.client.post(self.logout_url)
        replay = Client()
        replay.cookies[settings.SESSION_COOKIE_NAME] = old_cookie
        self.assert_requires_login(replay.get(self.workspace_url))
        self.assertContains(independent.get(self.workspace_url), "你好，learner_b")

    def test_get_cannot_logout_or_change_current_identity(self):
        self.login()
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 405)
        self.assertContains(self.client.get(self.workspace_url), "你好，learner_a")

    def test_missing_invalid_and_valid_csrf_logout(self):
        client = Client(enforce_csrf_checks=True)
        login_page = client.get(self.login_url)
        token = FormElements(login_page.content.decode()).inputs["csrfmiddlewaretoken"]["value"]
        self.assertEqual(client.post(self.login_url, {"username": "learner_a", "password": self.password, "csrfmiddlewaretoken": token}).status_code, 302)
        self.assertEqual(client.post(self.logout_url).status_code, 403)
        self.assertEqual(client.post(self.logout_url, {"csrfmiddlewaretoken": "invalid"}).status_code, 403)
        self.assertContains(client.get(self.workspace_url), "你好，learner_a")
        workspace = client.get(self.workspace_url)
        token = FormElements(workspace.content.decode()).inputs["csrfmiddlewaretoken"]["value"]
        self.assertRedirects(client.post(self.logout_url, {"csrfmiddlewaretoken": token}), self.home_url)
        self.assert_requires_login(client.get(self.workspace_url))

    def test_next_never_changes_logout_destination(self):
        for target in ("/workspace/", "https://example.com/other", "//example.com/other"):
            for source in ("query", "body"):
                with self.subTest(target=target, source=source):
                    client = Client()
                    self.login(client)
                    url, data = self.logout_url, {}
                    if source == "query":
                        url += "?" + urlencode({"next": target})
                    else:
                        data["next"] = target
                    self.assertRedirects(client.post(url, data), self.home_url)
                    self.assertNotIn(SESSION_KEY, client.session)

    def test_same_browser_can_logout_a_then_validate_and_login_b(self):
        self.login()
        self.assertContains(self.client.get(self.workspace_url), "你好，learner_a")
        self.client.post(self.logout_url)
        wrong = self.client.post(self.login_url, {"username": "learner_b", "password": "wrong-logout-test-password"})
        self.assertContains(wrong, "用户名或密码不正确")
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertRedirects(self.login(username="learner_b"), self.workspace_url)
        workspace = self.client.get(self.workspace_url)
        self.assertContains(workspace, "你好，learner_b")
        self.assertNotContains(workspace, "learner_a")

    def test_repeated_anonymous_post_is_safe(self):
        self.login()
        self.client.post(self.logout_url)
        self.assertRedirects(self.client.post(self.logout_url), self.home_url)
        self.assert_requires_login(self.client.get(self.workspace_url))
