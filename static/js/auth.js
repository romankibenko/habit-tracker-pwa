/** Логика экрана авторизации: переключение вкладок, регистрация, вход. */

import { api, ApiError, setToken, clearToken } from './api.js';

function showError(message) {
  const element = document.getElementById('auth-error');
  element.textContent = message;
  element.classList.remove('hidden');
}

function hideError() {
  document.getElementById('auth-error').classList.add('hidden');
}

export function bindAuthScreen({ onLoggedIn }) {
  const tabLogin = document.getElementById('tab-login');
  const tabRegister = document.getElementById('tab-register');
  const formLogin = document.getElementById('form-login');
  const formRegister = document.getElementById('form-register');

  function switchTab(target) {
    hideError();
    if (target === 'login') {
      tabLogin.classList.add('active');
      tabRegister.classList.remove('active');
      formLogin.classList.remove('hidden');
      formRegister.classList.add('hidden');
    } else {
      tabRegister.classList.add('active');
      tabLogin.classList.remove('active');
      formRegister.classList.remove('hidden');
      formLogin.classList.add('hidden');
    }
  }

  tabLogin.addEventListener('click', () => switchTab('login'));
  tabRegister.addEventListener('click', () => switchTab('register'));

  async function handleSubmit(event, method) {
    event.preventDefault();
    hideError();
    const form = event.currentTarget;
    const email = form.email.value.trim();
    const password = form.password.value;
    try {
      const data = await api[method](email, password);
      setToken(data.access_token);
      onLoggedIn(data);
    } catch (error) {
      if (error instanceof ApiError) {
        showError(error.message);
      } else {
        showError('Сеть недоступна. Попробуй позже.');
      }
    }
  }

  formLogin.addEventListener('submit', (e) => handleSubmit(e, 'login'));
  formRegister.addEventListener('submit', (e) => handleSubmit(e, 'register'));
}

export function logout() {
  clearToken();
  window.location.reload();
}
