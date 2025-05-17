import { fetchServers, excludeServers, includeServers } from './api.js';
import { renderGrid } from './grid.js';
import { showLoader, hideLoader } from './loader.js';
import { showListManager, loadListSelector } from './lists.js';

export async function init() {
  const config = JSON.parse(document.getElementById("config-data").textContent);

  // Загрузка и вставка header.html
  const headerHtml = await fetch("/static/components/header.html")
    .then(r => r.ok ? r.text() : Promise.reject("Header not found"));
  document.getElementById("header-container").innerHTML = headerHtml;

  // Инициализация обработчиков событий
  setupEventHandlers(config);

  // Загрузка списков и первая загрузка данных
  await loadListSelector();
  document.getElementById("list-selector")
          .addEventListener("change", () => loadAndRender(config));

  // Обработчик кликов по чекбоксам серверов
  document.addEventListener('change', (e) => {
    if (e.target.matches('#hosts-grid input[type="checkbox"]')) {
      updateBulkButtons();
    }
  });

  await loadAndRender(config);
}

function setupEventHandlers(config) {
  // Основные обработчики
  document.getElementById("showExcluded")
          .addEventListener("change", () => loadAndRender(config));

  // Обработчики выделения
  document.getElementById("select-all")
          .addEventListener("click", selectAll);
  document.getElementById("invert-selection")
          .addEventListener("click", invertSelection);
  document.getElementById("cancel-selection")
          .addEventListener("click", cancelSelection);

  // Обработчики действий с серверами
  document.getElementById("exclude-selected")
          .addEventListener("click", () => handleServerAction('exclude', config));
  document.getElementById("include-selected")
          .addEventListener("click", () => handleServerAction('include', config));
  document.getElementById("reset-filter")
          .addEventListener("click", () => handleServerAction('reset', config));
  document.getElementById("open-selected")
          .addEventListener("click", openSelected);
  document.addEventListener('update-tile', async (e) => {
           const { ip, config } = e.detail;
           await updateTile(ip, config);});

  // Обработчики работы со списками
  document.getElementById("add-to-list")
          .addEventListener("click", () => handleListAction('add'));
  document.getElementById("remove-from-list")
          .addEventListener("click", () => handleListAction('remove'));
  document.getElementById("manage-lists")
          .addEventListener("click", () => showListManager([], 'manage'));
}

function selectAll() {
  document.querySelectorAll('#hosts-grid input[type="checkbox"]')
          .forEach(cb => cb.checked = true);
  updateBulkButtons();
}

function invertSelection() {
  document.querySelectorAll('#hosts-grid input[type="checkbox"]')
          .forEach(cb => cb.checked = !cb.checked);
  updateBulkButtons();
}

function cancelSelection() {
  document.querySelectorAll('#hosts-grid input[type="checkbox"]')
          .forEach(cb => cb.checked = false);
  updateBulkButtons();
}

async function handleServerAction(action, config) {
  showLoader();
  try {
    switch(action) {
      case 'exclude':
        document.getElementById("showExcluded").checked = false;
        await excludeServers(getCheckedIPs());
        break;
      case 'include':
        document.getElementById("showExcluded").checked = false;
        await includeServers(getCheckedIPs());
        break;
      case 'reset':
        document.getElementById("showExcluded").checked = false;
        const all = await fetchServers(true);
        await includeServers(all.map(s => s.ip));
        break;
    }
    await loadAndRender(config);
  } catch (error) {
    console.error("Error handling server action:", error);
  } finally {
    hideLoader();
  }
}

function openSelected() {
  const config = JSON.parse(document.getElementById("config-data").textContent);
  document.querySelectorAll('#hosts-grid input[type="checkbox"]:checked')
          .forEach(cb => {
            const ip = cb.dataset.ip;
            const port = cb.dataset.wsPort;
            const url = `http://${ip}:${port}/vnc.html?` +
              `&autoconnect=true&resize=scale&compression=${config.VNC_COMPRESSION}` +
              `&scale=${config.VNC_FULLSCREEN_SCALE}&quality=${config.VNC_FULLSCREEN_QUALITY}`;
            window.open(url, '_blank');
          });
}

async function handleListAction(action) {
  const ips = getCheckedIPs();
  if (ips.length === 0) {
    alert("Выберите хотя бы один сервер");
    return;
  }
  showListManager(ips, action, true);
}

async function loadAndRender(config) {
  showLoader();
  try {
    const includeExcluded = document.getElementById("showExcluded").checked;
    const listName = document.getElementById("list-selector").value;

    let servers = await fetchServers(includeExcluded);

    if (listName !== "All Servers") {
      const lists = await fetch('/api/lists').then(r => r.json());
      const listServers = lists[listName] || [];
      servers = servers.filter(server => listServers.includes(server.ip));
    }

    if (includeExcluded) {
      servers = servers.filter(s => s.excluded);
    }

    await renderGrid(servers, config);
    updateBulkButtons();
  } catch (error) {
    console.error("Error loading servers:", error);
  } finally {
    hideLoader();
  }
}

function getCheckedIPs() {
  return Array.from(document.querySelectorAll('#hosts-grid input[type="checkbox"]:checked'))
              .map(cb => cb.dataset.ip);
}

async function updateBulkButtons() {
  const anyChecked = document.querySelectorAll('#hosts-grid input[type="checkbox"]:checked').length > 0;
  const hasCustomLists = await checkCustomListsExist();

  // Кнопки для работы со списками
  document.getElementById("add-to-list").style.display = (anyChecked && hasCustomLists) ? "inline-block" : "none";
  document.getElementById("remove-from-list").style.display = (anyChecked && hasCustomLists) ? "inline-block" : "none";

  // Остальные кнопки
  const showExcluded = document.getElementById("showExcluded").checked;
  document.getElementById("exclude-selected").style.display = (!showExcluded && anyChecked) ? "inline-block" : "none";
  document.getElementById("include-selected").style.display = (showExcluded && anyChecked) ? "inline-block" : "none";
  document.getElementById("open-selected").style.display = anyChecked ? "inline-block" : "none";
  document.getElementById("invert-selection").style.display = anyChecked ? "inline-block" : "none";
  document.getElementById("cancel-selection").style.display = anyChecked ? "inline-block" : "none";
}

async function checkCustomListsExist() {
  try {
    const res = await fetch('/api/lists');
    const lists = await res.json();
    return Object.keys(lists).filter(name => name !== "All Servers").length > 0;
  } catch (error) {
    console.error("Error checking custom lists:", error);
    return false;
  }
}