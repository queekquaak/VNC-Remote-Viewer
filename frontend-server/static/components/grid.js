import { hideLoader } from './loader.js';
import { checkHost, fetchServers } from './api.js';

const serverStates = new Map();

export async function renderGrid(servers, config) {
  const grid = document.getElementById("hosts-grid");
  const n = servers.length || 1;
  const cols = Math.min(Math.ceil(Math.sqrt(n)), 4);
  grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
  grid.innerHTML = '';

  servers.forEach(server => {
    serverStates.set(server.ip, {
      username: server.username,
      excluded: server.excluded
    });
  });

  for (const server of servers) {
    try {
      const isReachable = await checkHost(server.ip, server.websockify_port);
      if (!isReachable) {
        console.warn(`Host ${server.ip} is offline - skipping`);
        continue;
      }

      grid.appendChild(createTile(server, config));
    } catch (err) {
      console.warn(`Host ${server.ip} check failed:`, err);
    }
    await new Promise(r => setTimeout(r, 100));
  }

  if (!window.updateChecker) {
    startUpdateChecker(config);
  }

  updateBulkButtons();
  hideLoader();
}

function startUpdateChecker(config) {
  window.updateChecker = setInterval(async () => {
    try {
      const currentServers = await fetchServers(true);

      for (const server of currentServers) {
        const prevState = serverStates.get(server.ip);

        if (prevState && (
            prevState.username !== server.username ||
            prevState.excluded !== server.excluded
        )) {
          updateTile(server.ip, config);
          serverStates.set(server.ip, {
            username: server.username,
            excluded: server.excluded
          });
        }
      }
    } catch (error) {
      console.error("Update check failed:", error);
    }
  }, 5000);
}

function createTile(server, config) {
  const tile = document.createElement("div");
  tile.className = `tile ${server.excluded ? 'excluded' : ''}`;
  tile.dataset.ip = server.ip;

  const iframe = document.createElement("iframe");
  iframe.loading = "lazy";

  iframe.src = getViewOnlyUrl(server, config);

  iframe.style.width = '100%';
  iframe.style.height = '100%';
  iframe.style.objectFit = 'cover';

  const footer = document.createElement("div");
  footer.className = "tile-footer";

  const label = document.createElement("span");
  label.textContent = `${server.username} | host: ${server.ip}`;

  const right = document.createElement("div");
  right.className = "right";

  const openBtn = document.createElement("button");
  openBtn.className = "open-button";
  openBtn.textContent = "Открыть";
  openBtn.addEventListener("click", () => {
    window.open(getManagementUrl(server, config, true), '_blank');
  });

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.dataset.ip = server.ip;
  checkbox.dataset.wsPort = server.websockify_port;
  checkbox.addEventListener("change", updateBulkButtons);

  right.appendChild(openBtn);
  right.appendChild(checkbox);
  footer.appendChild(label);
  footer.appendChild(right);
  tile.appendChild(iframe);
  tile.appendChild(footer);

  return tile;
}

// URL для режима управления
function getManagementUrl(server, config, isFullscreen = false) {
  const params = new URLSearchParams({
    autoconnect: 'true',
    resize: 'scale',
    compression: config.VNC_COMPRESSION,
    scale: isFullscreen ? config.VNC_FULLSCREEN_SCALE : config.VNC_TILE_SCALE,
    quality: isFullscreen ? config.VNC_FULLSCREEN_QUALITY : config.VNC_TILE_QUALITY
  });
  return `http://${server.ip}:${server.websockify_port}/vnc.html?${params.toString()}`;
}

// URL для режима просмотра
function getViewOnlyUrl(server, config, isFullscreen = false) {
  const params = new URLSearchParams({
    password: config.VIEW_ONLY_PASS || '',
    autoconnect: 'true',
    resize: 'scale',
    view_only: 'true',
    compression: config.VNC_COMPRESSION,
    scale: isFullscreen ? config.VNC_FULLSCREEN_SCALE : config.VNC_TILE_SCALE,
    quality: isFullscreen ? config.VNC_FULLSCREEN_QUALITY : config.VNC_TILE_QUALITY
  });
  return `http://${server.ip}:${server.websockify_port}/vnc.html?${params.toString()}`;
}

export async function updateTile(ip, config) {
  const tile = document.querySelector(`.tile[data-ip="${ip}"]`);
  if (!tile) return;

  const scrollTop = tile.parentElement.scrollTop;
  const loader = document.createElement('div');
  loader.className = 'tile-loader';
  tile.innerHTML = '';
  tile.appendChild(loader);

  try {
    const servers = await fetchServers(true);
    const server = servers.find(s => s.ip === ip);
    if (!server) throw new Error("Server not found");

    const newTile = createTile(server, config);
    tile.replaceWith(newTile);
    newTile.parentElement.scrollTop = scrollTop;
  } catch (error) {
    console.error(`Error updating tile ${ip}:`, error);
    tile.innerHTML = '<div class="tile-error">Ошибка обновления</div>';
  }
}

function updateBulkButtons() {
  const checked = document.querySelectorAll('#hosts-grid input[type="checkbox"]:checked');
  const anyChecked = checked.length > 0;
  const showExcluded = document.getElementById("showExcluded").checked;

  document.getElementById("exclude-selected").style.display =
    (!showExcluded && anyChecked) ? "inline-block" : "none";
  document.getElementById("include-selected").style.display =
    (showExcluded && anyChecked) ? "inline-block" : "none";
  document.getElementById("open-selected").style.display =
    anyChecked ? "inline-block" : "none";
  document.getElementById("invert-selection").style.display =
    anyChecked ? "inline-block" : "none";
  document.getElementById("cancel-selection").style.display =
    anyChecked ? "inline-block" : "none";
}