"""T004 的登录 HTTP 集成；测试账号只在临时数据库中存在。"""

from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit

from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.sessions.models import Session
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.tests.test_forms import FormElements


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class LoginFlowTests(TestCase):
    password = "disposable-http-test-password"

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.user_a = user_model.objects.create_user("learner_a", password=cls.password)
        cls.user_b = user_model.objects.create_user("learner_b", password=cls.password)
        user_model.objects.create_user("inactive_learner", password=cls.password, is_active=False)

    def setUp(self):
        self.login_url = reverse("core:login")
        self.workspace_url = reverse("core:workspace")

    def login(self, client=None, username="learner_a", **extra):
        return (client or self.client).post(
            self.login_url, {"username": username, "password": self.password, **extra}
        )

    def stored_session(self, client=None):
        client = client or self.client
        return Session.objects.get(session_key=client.cookies[settings.SESSION_COOKIE_NAME].value)

    def test_public_home_has_login_entry_and_health_remains_public(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, f'href="{self.login_url}"')
        self.assertContains(response, "今天，给自己的成长留一点时间。")
        health = self.client.get(reverse("core:health"))
        self.assertEqual(health.json(), {"status": "ok"})

    def test_login_get_renders_form_and_uncached_response(self):
        response = self.client.get(self.login_url)
        elements = FormElements(response.content.decode())
        self.assertEqual(set(elements.inputs), {"username", "password", "csrfmiddlewaretoken"})
        self.assertContains(response, "欢迎回来")
        for text in ("注册", "找回密码", "记住我"):
            self.assertNotContains(response, text)
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_successful_login_reaches_workspace_with_current_identity(self):
        response = self.login()
        self.assertRedirects(response, self.workspace_url)
        self.assertEqual(self.client.session[SESSION_KEY], str(self.user_a.pk))
        workspace = self.client.get(self.workspace_url)
        self.assertContains(workspace, "我的工作台")
        self.assertContains(workspace, "你好，learner_a")
        self.assertNotContains(workspace, "learner_b")
        self.assertContains(workspace, "即将开放")
        self.assertIn("no-store", workspace.headers["Cache-Control"])
        self.assertIn("private", workspace.headers["Cache-Control"])
        home = self.client.get(reverse("core:home"))
        self.assertContains(home, f'href="{self.workspace_url}"')

    def test_invalid_credentials_show_generic_error_without_login(self):
        for username, password in (
            ("learner_a", "wrong-http-password"),
            ("missing_learner", self.password),
            ("inactive_learner", self.password),
        ):
            with self.subTest(username=username):
                client = Client()
                response = client.post(self.login_url, {"username": username, "password": password})
                self.assertContains(response, "用户名或密码不正确")
                elements = FormElements(response.content.decode())
                self.assertEqual(elements.inputs["username"]["value"], username)
                self.assertNotIn("value", elements.inputs["password"])
                self.assertNotContains(response, password)
                self.assertNotIn(SESSION_KEY, client.session)

    def test_required_input_errors_do_not_create_login(self):
        for username, password, messages in (
            ("", self.password, ("请输入用户名",)),
            ("learner_a", "", ("请输入密码",)),
            ("", "", ("请输入用户名", "请输入密码")),
        ):
            with self.subTest(messages=messages):
                client = Client()
                response = client.post(self.login_url, {"username": username, "password": password})
                for message in messages:
                    self.assertContains(response, message)
                self.assertNotIn(SESSION_KEY, client.session)

    @override_settings(LOGIN_URL="/unavailable-login/")
    def test_anonymous_workspace_uses_explicit_local_login_route(self):
        response = self.client.get(self.workspace_url)
        self.assertEqual(response.status_code, 302)
        destination = urlsplit(response.headers["Location"])
        self.assertEqual(destination.path, self.login_url)
        self.assertEqual(parse_qs(destination.query)["next"], [self.workspace_url])
        self.assertNotIn(b"learner_a", response.content)
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_workspace_ignores_client_supplied_identity(self):
        self.login()
        response = self.client.get(
            self.workspace_url, {"username": "learner_b", "user_id": self.user_b.pk}
        )
        self.assertContains(response, "你好，learner_a")
        self.assertNotContains(response, "learner_b")

    def test_two_independent_clients_display_their_own_identity(self):
        client_a, client_b = Client(), Client()
        self.login(client_a, "learner_a")
        self.login(client_b, "learner_b")
        response_a = client_a.get(self.workspace_url)
        response_b = client_b.get(self.workspace_url)
        self.assertContains(response_a, "你好，learner_a")
        self.assertNotContains(response_a, "learner_b")
        self.assertContains(response_b, "你好，learner_b")
        self.assertNotContains(response_b, "learner_a")
        self.assertNotEqual(self.stored_session(client_a).session_key, self.stored_session(client_b).session_key)

    def test_authenticated_login_redirects_without_renewing_deadline(self):
        self.login()
        original_deadline = self.stored_session().expire_date
        for target in ("/", "https://example.com/other"):
            response = self.client.get(self.login_url, {"next": target})
            self.assertRedirects(response, self.workspace_url)
        self.assertRedirects(self.login(next="/"), self.workspace_url)
        self.assertEqual(self.stored_session().expire_date, original_deadline)

    def test_next_parameters_never_change_success_destination(self):
        for target in ("/", "https://example.com/other", "http://testserver/"):
            for source in ("query", "body"):
                with self.subTest(target=target, source=source):
                    client = Client()
                    data = {"username": "learner_a", "password": self.password}
                    url = self.login_url
                    if source == "query":
                        url += "?" + urlencode({"next": target})
                    else:
                        data["next"] = target
                    self.assertRedirects(client.post(url, data), self.workspace_url)

    def test_csrf_is_required_for_login(self):
        client = Client(enforce_csrf_checks=True)
        data = {"username": "learner_a", "password": self.password}
        self.assertEqual(client.post(self.login_url, data).status_code, 403)
        page = client.get(self.login_url)
        token = FormElements(page.content.decode()).inputs["csrfmiddlewaretoken"]["value"]
        self.assertEqual(client.post(self.login_url, {**data, "csrfmiddlewaretoken": "invalid"}).status_code, 403)
        self.assertNotIn(SESSION_KEY, client.session)
        self.assertRedirects(client.post(self.login_url, {**data, "csrfmiddlewaretoken": token}), self.workspace_url)

    def test_success_sets_absolute_seven_day_deadline_and_persistent_cookie(self):
        start = timezone.now()
        with patch("core.views.timezone.now", return_value=start):
            response = self.login()
            self.assertEqual(response.status_code, 302)
            self.assertEqual(self.stored_session().expire_date, start + timedelta(days=7))
        cookie = response.cookies[settings.SESSION_COOKIE_NAME]
        self.assertEqual(cookie["max-age"], 604800)
        self.assertTrue(cookie["expires"])
        self.assertTrue(cookie["httponly"])

    def test_authenticated_workspace_only_accepts_get(self):
        self.login()
        self.assertEqual(self.client.post(self.workspace_url, {"username": "learner_b"}).status_code, 405)
