from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views import View
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, UserProfileForm, EmailAuthenticationForm
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
            # Логин сразу после регистрации
            login(request, user)
            messages.success(request, "Регистрация прошла успешно!")
            # --- Изменение: перенаправление на главную страницу ---
            return redirect('shop:catalog')
    else:
        form = CustomUserCreationForm()
        profile_form = UserProfileForm()
    return render(request, 'accounts/register.html', {'form': form, 'profile_form': profile_form})

# Кастомный LoginView
class CustomLoginView(LoginView):
    form_class = EmailAuthenticationForm
    template_name = 'accounts/login.html'

    # --- Изменение: переопределяем get_success_url ---
    def get_success_url(self):
        # Проверяем, является ли вошедший пользователь суперпользователем
        if self.request.user.is_superuser:
            # Перенаправляем в админ-панель
            return reverse_lazy('admin:index')
        else:
            # Для обычных пользователей - на главную страницу каталога
            return reverse_lazy('shop:catalog')

    def form_valid(self, form):
        # Вызываем стандартное поведение
        response = super().form_valid(form)
        # Добавляем сообщение после успешного входа
        messages.success(self.request, "Вы успешно вошли в систему.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Ошибка входа. Проверьте email и пароль.")
        return super().form_invalid(form)

# Кастомный LogoutView - НЕ наследуется от django.contrib.auth.views.LogoutView
class CustomLogoutView(View):
    def get(self, request, *args, **kwargs):
        # Выполняем стандартный logout вручную
        logout(request)
        # Возвращаем редирект на главную страницу
        from django.urls import reverse
        return HttpResponseRedirect(reverse('shop:catalog')) # Или HttpResponseRedirect('/') для корня

@login_required
def profile(request):
    profile_instance, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлен.")
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile_instance)

    return render(request, 'accounts/profile.html', {'form': form})