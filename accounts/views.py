from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
import secrets
import string
from .forms import CustomUserCreationForm, UserProfileForm, EmailAuthenticationForm, CustomPasswordChangeForm
from .models import UserProfile

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        if form.is_valid() and profile_form.is_valid():
            user = form.save() # Логика сохранения в форме
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            # --- ИЗМЕНЕНО: указываем EmailBackend при login ---
            # Так как аутентификация в приложении работает по email через EmailBackend
            login(request, user, backend='accounts.backends.EmailBackend')
            # --- /ИЗМЕНЕНО ---
            messages.success(request, "Регистрация прошла успешно!")
            return redirect('shop:catalog')
    else:
        form = CustomUserCreationForm()
        profile_form = UserProfileForm()
    return render(request, 'accounts/register.html', {'form': form, 'profile_form': profile_form})

# Кастомный LoginView
class CustomLoginView(LoginView):
    form_class = EmailAuthenticationForm
    template_name = 'accounts/login.html'

    def get_success_url(self):
        if self.request.user.is_superuser:
            return reverse_lazy('admin:index')
        else:
            return reverse_lazy('shop:catalog')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Вы успешно вошли в систему.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Ошибка входа. Проверьте email и пароль.")
        return super().form_invalid(form)

# Кастомный LogoutView - НЕ наследуется от django.contrib.auth.views.LogoutView
class CustomLogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        from django.urls import reverse
        return HttpResponseRedirect(reverse('shop:catalog'))

@login_required
def profile(request):
    profile_instance, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile_instance, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлен.")
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile_instance, user=request.user)

    return render(request, 'accounts/profile.html', {'form': form})

# Представление для смены пароля
class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:profile') # Перенаправление после смены

    def form_valid(self, form):
        messages.success(self.request, "Ваш пароль был успешно изменён.")
        return super().form_valid(form)

# Функция для восстановления пароля (сброс)
def reset_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Пользователь с таким email не найден.")
            return render(request, 'accounts/password_reset.html')

        # Генерация нового пароля
        alphabet = string.ascii_letters + string.digits
        new_password = ''.join(secrets.choice(alphabet) for _ in range(8))

        # Установка нового пароля
        user.set_password(new_password)
        user.save()

        # Отправка email (замените на реальный SMTP сервер в settings.py для продакшена)
        try:
            send_mail(
                subject='Восстановление пароля',
                message=f'Ваш новый пароль: {new_password}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            messages.success(request, "Новый пароль отправлен на ваш email.")
        except Exception as e:
            # В реальном приложении логгируйте ошибку и не показывайте детали пользователю
            messages.error(request, "Ошибка при отправке email. Пожалуйста, попробуйте позже.")
            # Лучше отправлять общий ответ, чтобы не раскрывать информацию о существовании аккаунта
            # messages.success(request, "Если аккаунт существует, инструкции отправлены на email.")

        return redirect('accounts:login')

    return render(request, 'accounts/password_reset.html')
