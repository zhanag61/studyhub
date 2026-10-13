"""T002：登录表单与模板；账号只存在于一次性测试数据库。"""

from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, override_settings

from core.forms import StudyHubAuthenticationForm


class FormElements(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.inputs = {}
        self.labels = set()
        self.ids = set()
        self.forms = []
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "input":
            self.inputs[attrs.get("name")] = attrs
        elif tag == "label":
            self.labels.add(attrs.get("for"))
        elif tag == "form":
            self.forms.append(attrs)


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class StudyHubAuthenticationFormTests(TestCase):
    password = "disposable-form-test-password"

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.user = user_model.objects.create_user(
            username="form_learner", password=cls.password
        )
        user_model.objects.create_user(
            username="form_inactive", password=cls.password, is_active=False
        )

    def setUp(self):
        self.request = RequestFactory().get("/login/")
        self.request.user = AnonymousUser()
        self.request.session = {}

    def make_form(self, username="form_learner", password=None):
        return StudyHubAuthenticationForm(
            self.request,
            data={
                "username": username,
                "password": self.password if password is None else password,
            },
        )

    def render_form(self, form):
        return render_to_string(
            "core/login.html", {"form": form}, request=self.request
        )

    def test_valid_credentials_identify_user_without_logging_in(self):
        form = self.make_form()
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_user().pk, self.user.pk)
        self.assertIs(form.request, self.request)
        self.assertEqual(self.request.session, {})
        self.assertFalse(self.request.user.is_authenticated)

    def test_empty_inputs_have_specific_required_errors(self):
        cases = (
            ("", self.password, {"username": "请输入用户名"}),
            ("form_learner", "", {"password": "请输入密码"}),
            ("", "", {"username": "请输入用户名", "password": "请输入密码"}),
        )
        for username, password, expected in cases:
            with self.subTest(fields=list(expected)):
                form = self.make_form(username, password)
                self.assertFalse(form.is_valid())
                self.assertEqual(set(form.errors), set(expected))
                for field, message in expected.items():
                    self.assertEqual(list(form.errors[field]), [message])
                self.assertIsNone(form.get_user())

    def test_invalid_credentials_share_message_and_clear_rendered_password(self):
        cases = (
            ("form_learner", "wrong-form-password"),
            ("form_missing", self.password),
            ("form_inactive", self.password),
        )
        for username, password in cases:
            with self.subTest(username=username):
                form = self.make_form(username, password)
                self.assertFalse(form.is_valid())
                self.assertEqual(
                    list(form.non_field_errors()), ["用户名或密码不正确"]
                )
                html = self.render_form(form)
                elements = FormElements(html)
                self.assertEqual(elements.inputs["username"]["value"], username)
                self.assertNotIn("value", elements.inputs["password"])
                self.assertNotIn(password, html)
                self.assertIsNone(form.get_user())

    @override_settings(
        AUTHENTICATION_BACKENDS=[
            "django.contrib.auth.backends.AllowAllUsersModelBackend"
        ]
    )
    def test_inactive_user_rejected_even_when_backend_returns_it(self):
        form = self.make_form("form_inactive")
        self.assertFalse(form.is_valid())
        self.assertEqual(list(form.non_field_errors()), ["用户名或密码不正确"])

    def test_password_keeps_leading_and_trailing_spaces(self):
        password = "  disposable-spaced-password  "
        user = get_user_model().objects.create_user(
            username="form_spaces", password=password
        )
        form = self.make_form(user.username, password)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_user().pk, user.pk)

    def test_valid_bound_form_also_never_renders_password_value(self):
        form = self.make_form()
        self.assertTrue(form.is_valid())
        html = self.render_form(form)
        self.assertNotIn(self.password, html)
        self.assertNotIn("value", FormElements(html).inputs["password"])

    def test_unbound_template_has_labels_autocomplete_and_csrf(self):
        html = self.render_form(StudyHubAuthenticationForm(self.request))
        elements = FormElements(html)
        self.assertIn("欢迎回来", html)
        self.assertEqual(
            set(elements.inputs), {"username", "password", "csrfmiddlewaretoken"}
        )
        for name, autocomplete in (
            ("username", "username"), ("password", "current-password")
        ):
            field = elements.inputs[name]
            self.assertIn(field["id"], elements.labels)
            self.assertEqual(field["autocomplete"], autocomplete)
            self.assertIn("required", field)
        self.assertEqual(elements.inputs["password"]["type"], "password")
        self.assertTrue(elements.inputs["csrfmiddlewaretoken"]["value"])
        self.assertEqual(elements.forms[0]["method"], "post")
        self.assertIn("novalidate", elements.forms[0])
        self.assertNotIn('type="checkbox"', html)
        for excluded in ("注册", "找回密码", "记住我"):
            self.assertNotIn(excluded, html)

    def test_required_errors_are_linked_to_inputs(self):
        form = self.make_form("", "")
        self.assertFalse(form.is_valid())
        html = self.render_form(form)
        elements = FormElements(html)
        for name in ("username", "password"):
            field = elements.inputs[name]
            self.assertEqual(field["aria-invalid"], "true")
            self.assertIn(field["id"], elements.labels)
            for described_id in field["aria-describedby"].split():
                self.assertIn(described_id, elements.ids)
        self.assertIn("请输入用户名", html)
        self.assertIn("请输入密码", html)

    def test_username_with_html_characters_is_escaped(self):
        username = '\"><script>alert("form-test")</script>'
        form = self.make_form(username, "wrong-form-password")
        self.assertFalse(form.is_valid())
        html = self.render_form(form)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertEqual(FormElements(html).inputs["username"]["value"], username)
