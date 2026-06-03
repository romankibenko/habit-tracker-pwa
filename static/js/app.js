/** Главный контроллер: роутинг между экранами, биндинг событий. */

import { api, ApiError, getToken } from './api.js';
import { bindAuthScreen, logout } from './auth.js';
import { renderHabitsList } from './habits.js';
import { bindStatsModal } from './stats.js';
import { enablePushNotifications } from './push.js';
import { bindInstallPrompt } from './install.js';
import { toast } from './toast.js';

const screens = {
  auth: document.getElementById('screen-auth'),
  app: document.getElementById('screen-app'),
};

function showScreen(name) {
  Object.entries(screens).forEach(([key, element]) => {
    element.classList.toggle('hidden', key !== name);
  });
}

function showModal(id) {
  document.getElementById(id).classList.remove('hidden');
}
function hideModal(id) {
  document.getElementById(id).classList.add('hidden');
}

function bindModalCloseButtons() {
  document.querySelectorAll('[data-close]').forEach((element) => {
    element.addEventListener('click', () => {
      hideModal(element.dataset.close);
    });
  });
}

function bindNewHabitForm() {
  const button = document.getElementById('btn-new-habit');
  const modal = 'modal-habit';
  const form = document.getElementById('form-habit');

  button.addEventListener('click', () => {
    form.reset();
    form.habit_id.value = '';
    document.getElementById('modal-habit-title').textContent = 'Новая привычка';
    showModal(modal);
    form.name.focus();
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = {
      name: form.name.value.trim(),
      description: form.description.value.trim() || null,
      color: form.color.value,
      target_per_week: Number(form.target_per_week.value),
    };
    try {
      await api.createHabit(payload);
      hideModal(modal);
      toast('Привычка добавлена');
      await renderHabitsList();
    } catch (error) {
      toast(error.message || 'Ошибка');
    }
  });
}

function bindLogout() {
  document.getElementById('btn-logout').addEventListener('click', logout);
}

function bindEnablePush() {
  document.getElementById('btn-enable-push').addEventListener('click', async () => {
    try {
      await enablePushNotifications();
    } catch (error) {
      toast(error.message || 'Не удалось включить уведомления');
    }
  });
}

async function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return;
  try {
    await navigator.serviceWorker.register('/service-worker.js');
    console.info('[PWA] service worker зарегистрирован');
  } catch (error) {
    console.warn('[PWA] не удалось зарегистрировать SW:', error);
  }
}

async function bootstrap() {
  bindModalCloseButtons();
  bindAuthScreen({
    onLoggedIn: (data) => enterApp(data.email),
  });
  bindStatsModal({ onHabitDeleted: () => renderHabitsList() });
  bindNewHabitForm();
  bindLogout();
  bindEnablePush();
  bindInstallPrompt();

  await registerServiceWorker();

  const token = getToken();
  if (!token) {
    showScreen('auth');
    return;
  }

  // Пробуем загрузить привычки — если токен протух, упадём в 401
  try {
    await enterApp();
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      logout();
    } else {
      console.error(error);
      toast('Ошибка загрузки данных');
      showScreen('auth');
    }
  }
}

async function enterApp(email) {
  showScreen('app');
  if (email) {
    document.getElementById('user-email').textContent = email;
  }
  await renderHabitsList();
}

bootstrap();
