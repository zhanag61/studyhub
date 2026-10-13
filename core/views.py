from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .forms import StudyHubAuthenticationForm

# 第一课的小练习：修改引号里的文字，保存后刷新浏览器。
WELCOME_MESSAGE = "今天，给自己的成长留一点时间。"


def home(request):
    """把 Python 中的首页文案交给 HTML 模板。"""
    return render(request, "core/home.html", {"welcome_message": WELCOME_MESSAGE})


class StudyHubLoginView(LoginView):
    template_name = "core/login.html"
    authentication_form = StudyHubAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        # 本轮只有一个登录目的地，不采用客户端传来的 next。
        return reverse("core:workspace")

    def form_valid(self, form):
        response = super().form_valid(form)
        # 只在成功登录时设置绝对截止时间，浏览不重新计时。
        self.request.session.set_expiry(timezone.now() + timedelta(days=7))
        return response


@never_cache
@login_required(login_url="core:login")
@require_GET
def workspace(request):
    """当前身份由认证中间件恢复，页面不接受客户端指定的用户名。"""
    return render(request, "core/workspace.html")


def health(request):
    """M0 只检查进程可响应；后续业务发布再加入数据库就绪检查。"""
    return JsonResponse({"status": "ok"}, headers={"Cache-Control": "no-store"})
