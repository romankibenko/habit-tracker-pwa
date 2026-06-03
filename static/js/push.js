/** Регистрация подписки на Web Push через VAPID. */

import { api } from './api.js';
import { toast } from './toast.js';

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  const output = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i++) output[i] = rawData.charCodeAt(i);
  return output;
}

export async function enablePushNotifications() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    toast('Браузер не поддерживает Web Push');
    return false;
  }

  const { public_key: publicKey } = await api.vapidPublicKey();
  if (!publicKey) {
    toast('Сервер не настроен для push-уведомлений');
    return false;
  }

  const permission = await Notification.requestPermission();
  if (permission !== 'granted') {
    toast('Разрешение на уведомления не получено');
    return false;
  }

  const registration = await navigator.serviceWorker.ready;
  let subscription = await registration.pushManager.getSubscription();
  if (!subscription) {
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicKey),
    });
  }

  const payload = subscription.toJSON();
  await api.pushSubscribe({
    endpoint: payload.endpoint,
    keys: { p256dh: payload.keys.p256dh, auth: payload.keys.auth },
  });

  toast('Уведомления включены');

  // Сразу шлём тестовый пуш для проверки
  try {
    await api.pushTest({ title: 'Habit Tracker', body: 'Пуши работают!' });
  } catch (error) {
    // не критично
  }

  return true;
}
