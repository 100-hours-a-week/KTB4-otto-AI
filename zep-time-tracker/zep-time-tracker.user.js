// ==UserScript==
// @name         ZEP Daily Time Tracker Manual Checkout
// @namespace    http://tampermonkey.net/
// @version      7.0
// @description  ZEP 접속 시간을 자동으로 시작하고, 퇴근 버튼을 눌러야 하루 기록을 마무리합니다.
// @match        https://zep.us/play/*
// @run-at       document-idle
// @grant        GM_getValue
// @grant        GM_setValue
// ==/UserScript==

(function () {
  'use strict';

  const STORAGE_KEY = 'zep_daily_time_records_v6';
  const STATE_KEY = 'zep_daily_time_state_v7';
  const POSITION_KEY = 'zep_time_tracker_panel_position_v2';

  let activeKey = null;
  let lastTickTime = Date.now();
  let lastPerformanceTime = performance.now();

  let panel = null;
  let recordsVisible = false;

  let titleArea = null;
  let dateArea = null;
  let timeArea = null;
  let secondsArea = null;
  let statusArea = null;
  let buttonArea = null;
  let recordsArea = null;

  function getTodayKey() {
    return new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Seoul',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(new Date());
  }

  function nowText() {
    return new Date().toISOString();
  }

  function normalizeRecords(records) {
    const normalized = {};

    Object.keys(records || {}).forEach(function (key) {
      const value = records[key];

      if (typeof value === 'number') {
        normalized[key] = {
          ms: value,
          checkedOut: false,
          startedAt: null,
          endedAt: null,
        };
      } else if (value && typeof value === 'object') {
        normalized[key] = {
          ms: Number(value.ms || 0),
          checkedOut: Boolean(value.checkedOut),
          startedAt: value.startedAt || null,
          endedAt: value.endedAt || null,
        };
      }
    });

    return normalized;
  }

  function loadRecords() {
    const saved = GM_getValue(STORAGE_KEY, '{}');

    try {
      return normalizeRecords(JSON.parse(saved));
    } catch (error) {
      return {};
    }
  }

  function saveRecords(records) {
    GM_setValue(STORAGE_KEY, JSON.stringify(records));
  }

  function loadState() {
    const saved = GM_getValue(STATE_KEY, '{}');

    try {
      return JSON.parse(saved);
    } catch (error) {
      return {};
    }
  }

  function saveState(state) {
    GM_setValue(STATE_KEY, JSON.stringify(state));
  }

  function loadPosition() {
    const saved = GM_getValue(POSITION_KEY, '');

    try {
      return saved ? JSON.parse(saved) : null;
    } catch (error) {
      return null;
    }
  }

  function savePosition(left, top) {
    GM_setValue(POSITION_KEY, JSON.stringify({ left, top }));
  }

  function ensureRecord(records, key) {
    if (!records[key]) {
      records[key] = {
        ms: 0,
        checkedOut: false,
        startedAt: nowText(),
        endedAt: null,
      };
    }

    if (!records[key].startedAt) {
      records[key].startedAt = nowText();
    }

    return records[key];
  }

  function startWorkday(key) {
    const records = loadRecords();
    const record = ensureRecord(records, key);

    record.checkedOut = false;
    record.endedAt = null;

    saveRecords(records);

    activeKey = key;
    saveState({
      activeKey: key,
      lastClosedKey: null,
    });

    lastTickTime = Date.now();
    lastPerformanceTime = performance.now();

    updatePanel();
  }

  function setupAutoStart() {
    const today = getTodayKey();
    const records = loadRecords();
    const state = loadState();

    if (state.activeKey && records[state.activeKey] && !records[state.activeKey].checkedOut) {
      activeKey = state.activeKey;
    } else if (records[today] && !records[today].checkedOut) {
      activeKey = today;
      saveState({
        activeKey: today,
        lastClosedKey: null,
      });
    } else if (state.lastClosedKey === today && records[today] && records[today].checkedOut) {
      activeKey = null;
    } else {
      startWorkday(today);
      return;
    }

    lastTickTime = Date.now();
    lastPerformanceTime = performance.now();
  }

  function addTime(key, ms) {
    if (!key || ms <= 0) return;

    const records = loadRecords();
    const record = ensureRecord(records, key);

    if (record.checkedOut) return;

    record.ms += ms;
    saveRecords(records);
  }

  function formatTime(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    return `${hours}시간 ${minutes}분 ${seconds}초`;
  }

  function getActiveTotalTime() {
    if (!activeKey) return 0;

    const records = loadRecords();
    const record = records[activeKey];

    return record ? record.ms : 0;
  }

  function createButton(text, onClick) {
    const button = document.createElement('button');

    button.textContent = text;
    button.style.border = 'none';
    button.style.borderRadius = '7px';
    button.style.padding = '4px 6px';
    button.style.margin = '2px';
    button.style.cursor = 'pointer';
    button.style.fontSize = '11px';
    button.style.background = '#ffffff';
    button.style.color = '#111111';

    button.addEventListener('click', function (event) {
      event.stopPropagation();
      onClick();
    });

    return button;
  }

  function makeDraggable() {
    let isDragging = false;
    let startMouseX = 0;
    let startMouseY = 0;
    let startLeft = 0;
    let startTop = 0;

    titleArea.addEventListener('mousedown', function (event) {
      isDragging = true;

      const rect = panel.getBoundingClientRect();

      startMouseX = event.clientX;
      startMouseY = event.clientY;
      startLeft = rect.left;
      startTop = rect.top;

      panel.style.left = `${rect.left}px`;
      panel.style.top = `${rect.top}px`;
      panel.style.right = 'auto';

      titleArea.style.cursor = 'grabbing';

      event.preventDefault();
    });

    document.addEventListener('mousemove', function (event) {
      if (!isDragging) return;

      let newLeft = startLeft + event.clientX - startMouseX;
      let newTop = startTop + event.clientY - startMouseY;

      const panelWidth = panel.offsetWidth;
      const panelHeight = panel.offsetHeight;

      const maxLeft = window.innerWidth - panelWidth;
      const maxTop = window.innerHeight - panelHeight;

      newLeft = Math.max(0, Math.min(newLeft, maxLeft));
      newTop = Math.max(0, Math.min(newTop, maxTop));

      panel.style.left = `${newLeft}px`;
      panel.style.top = `${newTop}px`;
    });

    document.addEventListener('mouseup', function () {
      if (!isDragging) return;

      isDragging = false;
      titleArea.style.cursor = 'grab';

      const rect = panel.getBoundingClientRect();
      savePosition(rect.left, rect.top);
    });
  }

  function createPanel() {
    if (!document.body) {
      setTimeout(createPanel, 500);
      return;
    }

    panel = document.createElement('div');
    panel.id = 'zep-time-tracker-panel';

    panel.style.position = 'fixed';
    panel.style.zIndex = '999999';
    panel.style.width = '220px';
    panel.style.background = 'rgba(0, 0, 0, 0.84)';
    panel.style.color = 'white';
    panel.style.padding = '10px';
    panel.style.borderRadius = '11px';
    panel.style.fontSize = '12px';
    panel.style.fontFamily = 'Arial, sans-serif';
    panel.style.boxShadow = '0 4px 12px rgba(0,0,0,0.35)';
    panel.style.lineHeight = '1.45';
    panel.style.userSelect = 'none';

    const savedPosition = loadPosition();

    if (savedPosition) {
      panel.style.left = `${savedPosition.left}px`;
      panel.style.top = `${savedPosition.top}px`;
    } else {
      panel.style.top = '20px';
      panel.style.right = '20px';
    }

    titleArea = document.createElement('div');
    titleArea.style.fontSize = '14px';
    titleArea.style.fontWeight = 'bold';
    titleArea.style.cursor = 'grab';
    titleArea.style.marginBottom = '5px';
    titleArea.textContent = 'ZEP 시간 측정기 ⠿';

    dateArea = document.createElement('div');
    dateArea.style.color = '#cccccc';
    dateArea.style.fontSize = '11px';

    timeArea = document.createElement('div');
    timeArea.style.marginTop = '6px';
    timeArea.style.fontSize = '15px';
    timeArea.style.fontWeight = 'bold';

    secondsArea = document.createElement('div');
    secondsArea.style.marginTop = '3px';
    secondsArea.style.fontSize = '11px';

    statusArea = document.createElement('div');
    statusArea.style.marginTop = '3px';
    statusArea.style.fontSize = '11px';

    buttonArea = document.createElement('div');
    buttonArea.style.marginTop = '7px';

    recordsArea = document.createElement('div');
    recordsArea.style.marginTop = '8px';
    recordsArea.style.paddingTop = '7px';
    recordsArea.style.borderTop = '1px solid rgba(255,255,255,0.25)';
    recordsArea.style.fontSize = '11px';
    recordsArea.style.maxHeight = '130px';
    recordsArea.style.overflowY = 'auto';
    recordsArea.style.display = 'none';

    panel.appendChild(titleArea);
    panel.appendChild(dateArea);
    panel.appendChild(timeArea);
    panel.appendChild(secondsArea);
    panel.appendChild(statusArea);
    panel.appendChild(buttonArea);
    panel.appendChild(recordsArea);

    document.body.appendChild(panel);

    makeDraggable();
    updatePanel();
  }

  function checkout() {
    tick();

    if (!activeKey) return;

    const keyToClose = activeKey;
    const records = loadRecords();
    const record = ensureRecord(records, keyToClose);

    record.checkedOut = true;
    record.endedAt = nowText();

    saveRecords(records);

    activeKey = null;
    saveState({
      activeKey: null,
      lastClosedKey: keyToClose,
    });

    lastTickTime = Date.now();
    lastPerformanceTime = performance.now();

    updatePanel();
  }

  function resetCurrentRecord() {
    const targetKey = activeKey || getTodayKey();
    const records = loadRecords();

    records[targetKey] = {
      ms: 0,
      checkedOut: false,
      startedAt: nowText(),
      endedAt: null,
    };

    saveRecords(records);

    activeKey = targetKey;
    saveState({
      activeKey: targetKey,
      lastClosedKey: null,
    });

    lastTickTime = Date.now();
    lastPerformanceTime = performance.now();

    updatePanel();
  }

  function updateButtons() {
    buttonArea.innerHTML = '';

    const recordsButton = createButton(
      recordsVisible ? '숨기기' : '기록',
      function () {
        recordsVisible = !recordsVisible;
        updatePanel();
      }
    );

    const workButton = createButton(
      activeKey ? '퇴근' : '출근',
      function () {
        if (activeKey) {
          const ok = confirm('현재 기록을 마무리하고 퇴근 처리할까요?');

          if (!ok) return;

          checkout();
        } else {
          startWorkday(getTodayKey());
        }
      }
    );

    const resetButton = createButton('초기화', function () {
      const ok = confirm('현재 기록 시간을 0으로 초기화할까요?');

      if (!ok) return;

      resetCurrentRecord();
    });

    const resetAllButton = createButton('전체삭제', function () {
      const ok = confirm('모든 날짜의 ZEP 접속 기록을 삭제할까요?');

      if (!ok) return;

      saveRecords({});
      activeKey = null;
      saveState({
        activeKey: null,
        lastClosedKey: null,
      });

      startWorkday(getTodayKey());
    });

    buttonArea.appendChild(recordsButton);
    buttonArea.appendChild(workButton);
    buttonArea.appendChild(resetButton);
    buttonArea.appendChild(resetAllButton);
  }

  function updateRecordsArea() {
    recordsArea.innerHTML = '';

    if (!recordsVisible) {
      recordsArea.style.display = 'none';
      return;
    }

    recordsArea.style.display = 'block';

    const records = loadRecords();
    const dates = Object.keys(records).sort().reverse();

    if (dates.length === 0) {
      recordsArea.textContent = '아직 기록이 없습니다.';
      return;
    }

    dates.forEach(function (dateKey) {
      const row = document.createElement('div');
      row.style.marginBottom = '5px';

      const record = records[dateKey];
      const secondsValue = Math.floor(record.ms / 1000);
      const label = record.checkedOut ? '완료' : '진행중';

      row.textContent = `${dateKey}: ${formatTime(record.ms)} / ${secondsValue}초 (${label})`;
      recordsArea.appendChild(row);
    });
  }

  function updatePanel() {
    if (!panel) return;

    const today = getTodayKey();
    const state = loadState();
    const displayKey = activeKey || state.lastClosedKey || today;
    const records = loadRecords();
    const record = records[displayKey];

    const displayMs = activeKey ? getActiveTotalTime() : record ? record.ms : 0;
    const displaySeconds = Math.floor(displayMs / 1000);

    dateArea.textContent = `기록일 ${displayKey}`;
    timeArea.textContent = formatTime(displayMs);
    secondsArea.textContent = `총 ${displaySeconds}초`;

    if (activeKey) {
      statusArea.textContent = '상태: 계산 중';
      statusArea.style.color = '#9eff9e';
    } else {
      statusArea.textContent = '상태: 퇴근 완료';
      statusArea.style.color = '#ffcc66';
    }

    updateButtons();
    updateRecordsArea();
  }

  function tick() {
    const now = Date.now();
    const nowPerformance = performance.now();

    if (!activeKey) {
      lastTickTime = now;
      lastPerformanceTime = nowPerformance;
      updatePanel();
      return;
    }

    const records = loadRecords();

    if (!records[activeKey] || records[activeKey].checkedOut) {
      const closedKey = activeKey;

      activeKey = null;
      saveState({
        activeKey: null,
        lastClosedKey: closedKey,
      });

      updatePanel();
      return;
    }

    const realDiff = now - lastTickTime;
    const performanceDiff = nowPerformance - lastPerformanceTime;
    const sleepGap = realDiff - performanceDiff;

    if (realDiff > 0 && sleepGap < 5000) {
      addTime(activeKey, realDiff);
    }

    lastTickTime = now;
    lastPerformanceTime = nowPerformance;

    updatePanel();
  }

  setupAutoStart();
  createPanel();

  setInterval(tick, 1000);

  window.addEventListener('beforeunload', tick);
  window.addEventListener('pagehide', tick);

  updateButtons();
  tick();
})();
