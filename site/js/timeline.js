'use strict';

// ===== グローバル状態 =====
let ALL_EVENTS = [];
let COMPANIES = [];
let PERSONS = [];
let META = {};
let timeline = null;
let dataset = null;

// フィルタ状態
const filters = {
  companies: new Set(),
  types: new Set(),
  importance: new Set(['high', 'medium', 'low']),
  search: '',
  autoCollectedOnly: false,
};

// イベントタイプ一覧
const EVENT_TYPES = [
  { id: 'model_release', label: 'モデルリリース', icon: '🤖' },
  { id: 'announcement', label: '企業発表', icon: '📢' },
  { id: 'statement', label: '主要人物発言', icon: '💬' },
  { id: 'paper', label: '研究論文', icon: '📄' },
  { id: 'policy', label: '政策・規制', icon: '🏛️' },
];

// ===== 初期化 =====
async function init() {
  try {
    const resp = await fetch('data.json');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    ALL_EVENTS = data.events || [];
    COMPANIES = data.companies || [];
    PERSONS = data.persons || [];
    META = data.meta || {};

    // 全企業・タイプをフィルタのデフォルトとして有効化
    COMPANIES.forEach(c => filters.companies.add(c.id));
    EVENT_TYPES.forEach(t => filters.types.add(t.id));

    buildSidebar();
    buildTimeline();
    updateStats();

    document.getElementById('loading').style.display = 'none';
    document.getElementById('timeline-container').style.display = 'block';

    // ヘッダーにメタ情報
    const generatedAt = META.generated_at ? new Date(META.generated_at).toLocaleDateString('ja-JP') : '不明';
    document.getElementById('header-meta').textContent =
      `${META.total_events || 0}件 | 最終更新: ${generatedAt}`;

  } catch (err) {
    document.getElementById('loading').innerHTML =
      `<div class="icon">⚠️</div><p>data.jsonの読み込みに失敗しました</p><pre style="font-size:0.7rem;color:#f88">${err.message}</pre>`;
    console.error(err);
  }
}

// ===== サイドバー構築 =====
function buildSidebar() {
  buildSearch();
  buildCompanyFilters();
  buildTypeFilters();
  buildImportanceFilters();
}

function buildSearch() {
  const input = document.getElementById('search-input');
  input.addEventListener('input', (e) => {
    filters.search = e.target.value.toLowerCase();
    applyFilters();
  });
}

function buildCompanyFilters() {
  const container = document.getElementById('company-filters');
  container.innerHTML = '';

  // イベント数カウント
  const counts = {};
  ALL_EVENTS.forEach(e => { counts[e.company] = (counts[e.company] || 0) + 1; });

  COMPANIES.forEach(company => {
    const count = counts[company.id] || 0;
    if (count === 0) return;

    const item = document.createElement('label');
    item.className = 'filter-item';
    item.innerHTML = `
      <input type="checkbox" checked data-company="${company.id}">
      <span class="company-dot" style="background:${company.color}"></span>
      <span>${company.name}</span>
      <span class="filter-count">${count}</span>
    `;
    item.querySelector('input').addEventListener('change', (e) => {
      if (e.target.checked) filters.companies.add(company.id);
      else filters.companies.delete(company.id);
      applyFilters();
    });
    container.appendChild(item);
  });
}

function buildTypeFilters() {
  const container = document.getElementById('type-filters');
  container.innerHTML = '';

  const counts = {};
  ALL_EVENTS.forEach(e => { counts[e.type] = (counts[e.type] || 0) + 1; });

  EVENT_TYPES.forEach(type => {
    const count = counts[type.id] || 0;
    if (count === 0) return;

    const item = document.createElement('label');
    item.className = 'filter-item';
    item.innerHTML = `
      <input type="checkbox" checked data-type="${type.id}">
      <span>${type.icon} ${type.label}</span>
      <span class="filter-count">${count}</span>
    `;
    item.querySelector('input').addEventListener('change', (e) => {
      if (e.target.checked) filters.types.add(type.id);
      else filters.types.delete(type.id);
      applyFilters();
    });
    container.appendChild(item);
  });
}

function buildImportanceFilters() {
  const buttons = document.querySelectorAll('.imp-btn');
  buttons.forEach(btn => {
    btn.classList.add('active');
    btn.addEventListener('click', () => {
      const val = btn.dataset.importance;
      if (filters.importance.has(val)) {
        filters.importance.delete(val);
        btn.classList.remove('active');
      } else {
        filters.importance.add(val);
        btn.classList.add('active');
      }
      applyFilters();
    });
  });
}

// ===== タイムライン構築 =====
function buildTimeline() {
  const container = document.getElementById('vis-timeline');

  // グループ（企業ごとの行）
  const groups = new vis.DataSet(
    COMPANIES
      .filter(c => ALL_EVENTS.some(e => e.company === c.id))
      .map(c => ({
        id: c.id,
        content: `<span style="color:${c.color};font-weight:600">${c.name}</span>`,
        style: `background:var(--bg-card)`,
      }))
  );

  // グループにない企業のイベント用（person発言など）
  groups.add({ id: 'other', content: '<span style="color:#8b90a8">その他・人物</span>' });

  // アイテム
  dataset = new vis.DataSet(eventsToItems(ALL_EVENTS));

  const options = {
    orientation: 'top',
    stack: true,
    showMajorLabels: true,
    showMinorLabels: true,
    height: '100%',
    zoomMin: 1000 * 60 * 60 * 24 * 30,        // 最小ズーム: 1ヶ月
    zoomMax: 1000 * 60 * 60 * 24 * 365 * 10,   // 最大ズーム: 10年
    start: '2017-01-01',
    end: new Date().toISOString().slice(0, 10),
    tooltip: { followMouse: true, overflowMethod: 'cap' },
    locale: 'ja',
  };

  timeline = new vis.Timeline(container, dataset, groups, options);
  timeline.on('select', ({ items }) => {
    if (items.length > 0) showDetail(items[0]);
    else hideDetail();
  });
}

function eventsToItems(events) {
  return events.map(e => {
    const company = COMPANIES.find(c => c.id === e.company);
    const color = company ? company.color : '#8b90a8';
    const group = e.company || 'other';
    const icon = e.type_icon || '📌';

    // 重要度でサイズを変える
    const isHigh = e.importance === 'high';
    const bgAlpha = isHigh ? 'dd' : '99';

    return {
      id: e.id,
      group,
      start: e.date,
      content: `${icon} ${e.title.slice(0, 40)}${e.title.length > 40 ? '…' : ''}`,
      title: `<strong>${e.title}</strong><br>${e.date}`,
      style: [
        `background: ${color}${bgAlpha}`,
        `border-color: ${color}`,
        `color: white`,
        isHigh ? 'font-weight:600' : '',
      ].filter(Boolean).join(';'),
      className: `event-${e.type} importance-${e.importance}`,
      _event: e,  // 元データ参照用
    };
  });
}

// ===== フィルタ適用 =====
function applyFilters() {
  const filtered = ALL_EVENTS.filter(e => {
    if (!filters.companies.has(e.company) && e.company) return false;
    if (!filters.types.has(e.type)) return false;
    if (!filters.importance.has(e.importance)) return false;
    if (filters.search) {
      const searchable = `${e.title} ${e.description} ${e.company_name} ${e.person_name} ${e.tags.join(' ')}`.toLowerCase();
      if (!searchable.includes(filters.search)) return false;
    }
    return true;
  });

  dataset.clear();
  dataset.add(eventsToItems(filtered));
  updateStats(filtered.length);
}

// ===== 詳細パネル =====
function showDetail(itemId) {
  const item = dataset.get(itemId);
  if (!item) return;

  const e = item._event;
  const panel = document.getElementById('detail-panel');
  const company = COMPANIES.find(c => c.id === e.company);
  const person = PERSONS.find(p => p.id === e.person);

  panel.classList.remove('hidden');
  document.querySelector('.detail-placeholder')?.remove();

  document.getElementById('detail-title').textContent = e.title;

  // メタチップ
  const metaEl = document.getElementById('detail-meta');
  metaEl.innerHTML = '';
  metaEl.appendChild(makeChip(e.date, null));
  if (company) metaEl.appendChild(makeChip(company.name, company.color));
  if (person) metaEl.appendChild(makeChip(person.name, null));
  metaEl.appendChild(makeChip(e.type_icon + ' ' + e.type, null));
  metaEl.appendChild(makeChip(e.importance === 'high' ? '★ 重要' : e.importance === 'medium' ? '◆ 中' : '▪ 低', null));
  if (e.auto_collected) metaEl.appendChild(makeChip('🤖 自動収集', null));

  // 説明
  document.getElementById('detail-description').textContent = e.description;

  // タグ
  const tagsEl = document.getElementById('detail-tags');
  tagsEl.innerHTML = e.tags.map(t => `<span class="tag">${t}</span>`).join('');

  // ソースリンク
  const linkEl = document.getElementById('detail-link');
  if (e.source_url && e.source_url !== 'null') {
    linkEl.href = e.source_url;
    linkEl.style.display = 'inline-flex';
  } else {
    linkEl.style.display = 'none';
  }

  // 詳細本文
  const bodyEl = document.getElementById('detail-body-text');
  bodyEl.textContent = e.body || '';
  bodyEl.style.display = e.body ? 'block' : 'none';
}

function makeChip(text, color) {
  const span = document.createElement('span');
  span.className = 'meta-chip' + (color ? ' company' : '');
  span.textContent = text;
  if (color) span.style.background = color + 'cc';
  return span;
}

function hideDetail() {
  document.getElementById('detail-panel').classList.add('hidden');
}

// ===== 統計バー =====
function updateStats(shownCount) {
  const total = ALL_EVENTS.length;
  const shown = shownCount !== undefined ? shownCount : total;
  document.getElementById('stats-shown').textContent = shown;
  document.getElementById('stats-total').textContent = total;

  if (META.total_events) {
    const range = ALL_EVENTS.length > 0
      ? `${ALL_EVENTS[0]?.date?.slice(0,4)} 〜 ${ALL_EVENTS[ALL_EVENTS.length-1]?.date?.slice(0,4)}`
      : '';
    document.getElementById('stats-range').textContent = range;
  }
}

// ===== 今日へジャンプ =====
function jumpToToday() {
  if (timeline) timeline.moveTo(new Date());
}

// ===== 全体表示 =====
function fitAll() {
  if (timeline) timeline.fit();
}

// ===== 起動 =====
document.addEventListener('DOMContentLoaded', init);
