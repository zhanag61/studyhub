"""T005：可控时间验证固定期限，不改系统时间或真实数据库。"""

from contextlib import contextmanager
from datetime import timedelta
from email.utils import parsedate_to_datetime
from unittest.mock import patch
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.models import Session
from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class FixedSessionDeadlineTests(TestCase):
    password = "disposable-session-test-password"

    @classmethod
    def setUpTestData(cls):
        cls.user_a = get_user_model().objects.create_user("learner_a", password=cls.password)
        cls.user_b = get_user_model().objects.create_user("learner_b", password=cls.password)

    def setUp(self):
        self.start = timezone.now().replace(microsecond=0)
        self.deadline = self.start + timedelta(days=7)
        self.login_url = reverse("core:login")
        self.workspace_url = reverse("core:workspace")

    @contextmanager
    def at_time(self, when):
        # Django 的会话查询与 Cookie 日期都采用同一个模拟时钟。
        with (
            patch("django.utils.timezone.now", return_value=when),
            patch("django.contrib.sessions.middleware.time.time", return_value=when.timestamp()),
        ):
            yield

    def login_at(self, when, client=None, username="learner_a"):
        client = client or self.client
        with self.at_time(when):
            response = client.post(self.login_url, {"username": username, "password": self.password})
            self.assertRedirects(response, self.workspace_url)
        return response

    def stored_session(self, client=None):
        client = client or self.client
        return Session.objects.get(session_key=client.cookies[settings.SESSION_COOKIE_NAME].value)

    def assert_requires_login(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlsplit(response.headers["Location"]).path, self.login_url)
        self.assertNotIn("learner_a", response.content.decode())
        self.assertNotIn("learner_b", response.content.decode())

    def test_browsing_at_day_six_does_not_renew_deadline_or_cookie(self):
        login = self.login_at(self.start)
        cookie = login.cookies[settings.SESSION_COOKIE_NAME]
        self.assertEqual(parsedate_to_datetime(cookie["expires"]), self.deadline)
        self.assertEqual(cookie["max-age"], 604800)
        self.assertTrue(cookie["httponly"])
        original_key = cookie.value
        with self.at_time(self.start + timedelta(days=6)):
            for url in (reverse("core:home"), self.workspace_url, self.login_url):
                with self.subTest(url=url):
                    response = self.client.get(url)
                    if url == self.login_url:
                        self.assertRedirects(response, self.workspace_url)
                    else:
                        self.assertContains(response, "退出登录")
                    self.assertNotIn(settings.SESSION_COOKIE_NAME, response.cookies)
                    stored = self.stored_session()
                    self.assertEqual(stored.expire_date, self.deadline)
                    self.assertEqual(stored.session_key, original_key)
            self.assertContains(self.client.get(self.workspace_url), "你好，learner_a")

    def test_day_six_session_write_keeps_deadline_and_remaining_cookie_age(self):
        self.login_at(self.start)
        original_key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        with self.at_time(self.start + timedelta(days=6)):
            # 仅在测试请求中写一个普通会话字段，经过真实保存/Cookie 中间件；
            # 不增加产品路由，也不再次设置到期时间。
            request = RequestFactory().get(self.workspace_url)
            request.COOKIES[settings.SESSION_COOKIE_NAME] = original_key
            middleware = SessionMiddleware(lambda _: HttpResponse())
            middleware.process_request(request)
            self.assertEqual(request.session[SESSION_KEY], str(self.user_a.pk))
            request.session["test_note"] = "saved at day six"
            response = middleware.process_response(request, HttpResponse())
            cookie = response.cookies[settings.SESSION_COOKIE_NAME]
            self.assertEqual(cookie.value, original_key)
            self.assertEqual(cookie["max-age"], 86400)
            self.assertEqual(parsedate_to_datetime(cookie["expires"]), self.deadline)
            stored = self.stored_session()
            self.assertEqual(stored.expire_date, self.deadline)
            self.assertEqual(stored.get_decoded()["test_note"], "saved at day six")
            self.assertContains(self.client.get(self.workspace_url), "你好，learner_a")

    def test_exact_deadline_rejects_cookie_even_when_client_replays_it(self):
        self.login_at(self.start)
        old_cookie = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        with self.at_time(self.deadline - timedelta(seconds=1)):
            self.assertContains(self.client.get(self.workspace_url), "你好，learner_a")
        for when in (self.deadline, self.deadline + timedelta(seconds=1)):
            with self.subTest(when=when), self.at_time(when):
                replay = Client()
                # Client 不会自动丢弃到期 Cookie，因此必须由服务器拒绝它。
                replay.cookies[settings.SESSION_COOKIE_NAME] = old_cookie
                self.assert_requires_login(replay.get(self.workspace_url))
                self.assertNotIn(SESSION_KEY, replay.session)

    def test_login_after_expiry_starts_new_deadline_and_does_not_restore_old_cookie(self):
        self.login_at(self.start)
        old_cookie = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        later = self.deadline + timedelta(seconds=1)
        with self.at_time(later):
            self.assert_requires_login(self.client.get(self.workspace_url))
            response = self.login_at(later)
            new_cookie = response.cookies[settings.SESSION_COOKIE_NAME]
            self.assertNotEqual(new_cookie.value, old_cookie)
            self.assertEqual(self.stored_session().expire_date, later + timedelta(days=7))
            self.assertEqual(new_cookie["max-age"], 604800)
            replay = Client()
            replay.cookies[settings.SESSION_COOKIE_NAME] = old_cookie
            self.assert_requires_login(replay.get(self.workspace_url))
            self.assertContains(self.client.get(self.workspace_url), "你好，learner_a")

    def test_independent_sessions_expire_at_their_own_login_deadlines(self):
        self.login_at(self.start)
        independent = Client()
        self.login_at(self.start + timedelta(days=1), independent, "learner_b")
        with self.at_time(self.deadline):
            self.assert_requires_login(self.client.get(self.workspace_url))
            self.assertContains(independent.get(self.workspace_url), "你好，learner_b")
            self.assertEqual(self.stored_session(independent).expire_date, self.start + timedelta(days=8))
