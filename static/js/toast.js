/** Простейший тост-уведомитель. */

let timer = null;

export function toast(message, duration = 2500) {
  const element = document.getElementById('toast');
  if (!element) return;
  element.textContent = message;
  element.classList.remove('hidden');
  if (timer) clearTimeout(timer);
  timer = setTimeout(() => element.classList.add('hidden'), duration);
}
