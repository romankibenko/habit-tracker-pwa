/** Модалка детальной статистики + удаление привычки. */

import { api } from './api.js';
import { toast } from './toast.js';

let currentHabit = null;

function renderCalendar(last30Dates) {
  const container = document.getElementById('calendar-30');
  container.innerHTML = '';
  const doneSet = new Set(last30Dates);

  const today = new Date();
  for (let i = 29; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    const iso = d.toISOString().slice(0, 10);
    const isDone = doneSet.has(iso);

    const cell = document.createElement('div');
    cell.className = 'calendar-day' + (isDone ? ' done' : '');
    cell.title = iso;
    cell.textContent = d.getDate();
    container.appendChild(cell);
  }
}

export async function openStatsModal(habit) {
  currentHabit = habit;
  document.getElementById('stats-habit-name').textContent = habit.name;
  document.getElementById('stats-current-streak').textContent = '…';
  document.getElementById('stats-longest-streak').textContent = '…';
  document.getElementById('stats-total').textContent = '…';
  document.getElementById('calendar-30').innerHTML = '';

  document.getElementById('modal-stats').classList.remove('hidden');

  try {
    const stats = await api.habitStats(habit.id);
    document.getElementById('stats-current-streak').textContent = stats.current_streak;
    document.getElementById('stats-longest-streak').textContent = stats.longest_streak;
    document.getElementById('stats-total').textContent = stats.total_checkins;
    renderCalendar(stats.last_30_days);
  } catch (error) {
    toast(error.message || 'Не удалось загрузить статистику');
  }
}

export function bindStatsModal({ onHabitDeleted }) {
  document.getElementById('btn-delete-habit').addEventListener('click', async () => {
    if (!currentHabit) return;
    if (!confirm(`Удалить привычку «${currentHabit.name}»? История чекинов будет потеряна.`)) {
      return;
    }
    try {
      await api.deleteHabit(currentHabit.id);
      document.getElementById('modal-stats').classList.add('hidden');
      toast('Привычка удалена');
      onHabitDeleted();
    } catch (error) {
      toast(error.message || 'Ошибка');
    }
  });
}
