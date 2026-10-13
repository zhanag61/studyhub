"""StudyHub 的登录表单，沿用 Django 自带的认证流程。"""

from django.contrib.auth.forms import AuthenticationForm


class StudyHubAuthenticationForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "用户名或密码不正确",
        "inactive": "用户名或密码不正确",
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        username = self.fields["username"]
        username.label = "用户名"
        username.error_messages["required"] = "请输入用户名"
        username.widget.attrs.update(
            {
                "class": "login-input",
                "autocomplete": "username",
                "autocapitalize": "none",
                "spellcheck": "false",
            }
        )

        password = self.fields["password"]
        password.label = "密码"
        password.error_messages["required"] = "请输入密码"
        password.widget.attrs.update(
            {"class": "login-input", "autocomplete": "current-password"}
        )
        # 错误后重新显示表单时，不把提交的密码写回页面。
        password.widget.render_value = False
