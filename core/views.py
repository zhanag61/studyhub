from django.shortcuts import render

# 第一课的小练习：修改引号里的文字，保存后刷新浏览器。
WELCOME_MESSAGE = "今天，从一个小目标开始。"


def home(request):
    """把 Python 中的首页文案交给 HTML 模板。"""
    return render(request, "core/home.html", {"welcome_message": WELCOME_MESSAGE})
