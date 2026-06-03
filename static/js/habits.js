/** Рендер списка привычек, кнопки чекина, открытие модалок. */

import { api } from './api.js';
import { toast } from './toast.js';
import { openStatsModal } from './stats.js';

const todayISO = () => new Date().toISOString().slice(0, 10);

function makeCard(habit, checkinForToday) {
  const card = document.createElement('article');
  card.className = 'habit-card';
  card.dataset.habitId = habit.id;
  card.style.borderLeftColor = habit.color || '#4f46e5';

  const checked = Boolean(checkinForToday);
  card.innerHTML = `
    <div class="habit-card-header">
      <div>
        <div class="habit-name">${escapeHtml(habit.name)}</div>
        ${habit.description ? `<div class="habit-description">${escapeHtml(habit.description)}</div>` : ''}
      </div>
    </div>
    <div class="habit-actions">
      <button class="checkin-btn ${checked ? 'checked' : ''}" data-action="checkin">
        ${checked ? '✓ Сделано сегодня' : 'Отметить за сегодня'}
      </button>
      <button class="btn btn-ghost" data-action="stats" title="Статистика">📊</button>
    </div>
  `;

  card.addEventListener('click', async (event) => {
    const action = event.target.closest('[data-action]')?.dataset.action;
    if (action === 'checkin') {
      event.stopPropagation();
      await handleCheckin(habit, checkinForToday, card);
    } else if (action === 'stats') {
      event.stopPropagation();
      openStatsModal(habit);
    }
  });

  return card;
}

async function handleCheckin(habit, existingCheckin, card) {
  const button = card.querySelector('[data-action="checkin"]');
  button.disabled = true;
  try {
    if (existingCheckin) {
      await api.deleteCheckin(existingCheckin.id);
      button.classList.remove('checked');
      button.textContent = 'Отметить за сегодня';
      toast('Отметка снята');
      card.dataset.checkinId = '';
    } else {
      const created = await api.createCheckin({
        habit_id: habit.id,
        date: todayISO(),
      });
      button.classList.add('checked');
      button.textContent = '✓ Сделано сегодня';
      card.dataset.checkinId = created.id;
      toast('Молодец!');
    }
  } catch (error) {
    toast(error.message || 'Ошибка');
  } finally {
    button.disabled = false;
    // Перезагружаем список, чтобы стрик обновился, если в карточке отобразится
    await renderHabitsList();
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export async function renderHabitsList() {
  const grid = document.getElementById('habits-list');
  const emptyState = document.getElementById('habits-empty');
  const habits = await api.listHabits();
  const visibleHabits = habits.filter((h) => !h.is_archived);

  grid.innerHTML = '';

  if (visibleHabits.length === 0) {
    emptyState.classList.remove('hidden');
    return;
  }
  emptyState.classList.add('hidden');

  // Для каждой привычки тянем последний чекин (на сегодня)
  const today = todayISO();
  const checkinsByHabit = await Promise.all(
    visibleHabits.map((h) => api.listCheckins(h.id, 1).catch(() => []))
  );

  visibleHabits.forEach((habit, index) => {
    const todayCheckin = (checkinsByHabit[index] || []).find(
      (c) => c.date === today
    );
    grid.appendChild(makeCard(habit, todayCheckin));
  });
}
