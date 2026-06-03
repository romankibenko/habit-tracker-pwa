/** Перехват события установки PWA — деферится, чтобы можно было показать
 *  свою кнопку, если будет нужно. Сейчас просто логируем и сохраняем. */

let deferredPrompt = null;

export function bindInstallPrompt() {
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    deferredPrompt = event;
    console.info('[PWA] установка доступна — можно вызвать deferredPrompt.prompt()');
  });

  window.addEventListener('appinstalled', () => {
    console.info('[PWA] приложение установлено');
    deferredPrompt = null;
  });
}

export async function promptInstall() {
  if (!deferredPrompt) return false;
  deferredPrompt.prompt();
  const choice = await deferredPrompt.userChoice;
  deferredPrompt = null;
  return choice.outcome === 'accepted';
}
