from django.urls import path
from django.contrib.auth.views import LogoutView # Импортируем LogoutView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    # Указываем, куда перенаправлять после logout
    path('logout/', LogoutView.as_view(next_page='shop:catalog'), name='logout'), # Перенаправляем на главную
]