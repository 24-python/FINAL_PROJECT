from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .forms import CustomUserCreationForm, UserProfileForm, EmailAuthenticationForm

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
            return redirect('shop:catalog')
    else:
        form = CustomUserCreationForm()
        profile_form = UserProfileForm()
    return render(request, 'accounts/register.html', {'form': form, 'profile_form': profile_form})

# Кастомный LoginView
class CustomLoginView(LoginView):
    form_class = EmailAuthenticationForm
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        messages.success(self.request, "Вы успешно вошли в систему.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Ошибка входа. Проверьте email и пароль.")
        return super().form_invalid(form)