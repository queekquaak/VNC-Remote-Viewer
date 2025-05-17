export function showListManager(ips = [], action = 'manage', selectMode = false) {
  const modal = document.createElement('div');
  modal.className = 'list-modal';
  modal.style.zIndex = '10000';

  const modalTitle = selectMode ?
    (action === 'add' ? 'Добавить в списки' : 'Убрать из списков') :
    'Управление списками';

  modal.innerHTML = `
    <div class="modal-content">
      <h3>${modalTitle}</h3>
      <div id="lists-container" class="lists-container"></div>

      ${!selectMode ? `
        <div class="list-actions">
          <input type="text" id="new-list-name" placeholder="Название нового списка">
          <button id="create-list" class="btn green">Создать список</button>
          <button id="delete-selected-lists" class="btn red">Удалить выбранные</button>
        </div>
      ` : ''}

      <div class="modal-buttons">
        ${selectMode ? '<button id="confirm-action" class="btn blue">ОК</button>' : ''}
        <button id="cancel-lists" class="btn gray">Отмена</button>
      </div>
      <div id="list-loader" class="loader" style="display: none;"></div>
    </div>
  `;

  document.body.appendChild(modal);
  let listsData = {};

  // Функция для показа загрузки
  const showLoader = () => {
    const loader = modal.querySelector('#list-loader');
    if (loader) loader.style.display = 'block';
  };

  // Функция для скрытия загрузки
  const hideLoader = () => {
    const loader = modal.querySelector('#list-loader');
    if (loader) loader.style.display = 'none';
  };

  // Загрузка списков
  fetch('/api/lists')
    .then(res => res.json())
    .then(lists => {
      listsData = lists;
      renderLists(lists);
    })
    .catch(error => {
      console.error("Error loading lists:", error);
      modal.remove();
    });

  function renderLists(lists) {
    const container = document.getElementById('lists-container');
    container.innerHTML = '';

    if (Object.keys(lists).filter(name => name !== "All Servers").length === 0) {
      container.innerHTML = '<p class="no-lists">Нет пользовательских списков</p>';
      return;
    }

    for (const [name, items] of Object.entries(lists)) {
      if (name === "All Servers") continue;

      const div = document.createElement('div');
      div.className = 'list-item';

      const checked = selectMode ?
        (action === 'add' ? !ips.some(ip => items.includes(ip)) : ips.some(ip => items.includes(ip))) :
        false;

      div.innerHTML = `
        <label>
          <input type="checkbox" class="list-checkbox" data-list="${name}" ${checked ? 'checked' : ''}>
          <span class="list-name">${name}</span>
          <span class="server-count">(${items.length} серверов)</span>
        </label>
      `;
      container.appendChild(div);
    }
  }

  // Обработчики для режима выбора списков
  if (selectMode) {
    document.getElementById('confirm-action').addEventListener('click', async () => {
      const checkboxes = document.querySelectorAll('.list-checkbox:checked');
      const selectedLists = Array.from(checkboxes).map(cb => cb.dataset.list);

      if (selectedLists.length === 0) {
        modal.remove();
        return;
      }

      showLoader();
      try {
        const promises = selectedLists.map(list => {
          const currentList = listsData[list] || [];
          const serversToUpdate = action === 'add'
            ? ips.filter(ip => !currentList.includes(ip))
            : ips.filter(ip => currentList.includes(ip));

          if (serversToUpdate.length > 0) {
            return fetch('/api/lists', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({
                action: action,
                list_name: list,
                servers: serversToUpdate
              })
            });
          }
          return Promise.resolve();
        });

        await Promise.all(promises);
        modal.remove();
        window.location.reload();
      } catch (error) {
        console.error("Error updating lists:", error);
        alert("Ошибка при обновлении списков");
        hideLoader();
      }
    });
  } else {
    // Обработчики для режима управления списками
    document.getElementById('create-list').addEventListener('click', async () => {
      const name = document.getElementById('new-list-name').value.trim();
      if (!name) {
        alert("Введите название списка");
        return;
      }

      if (listsData[name]) {
        alert("Список с таким именем уже существует");
        return;
      }

      showLoader();
      try {
        const response = await fetch('/api/lists', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            action: 'add',
            list_name: name,
            servers: []
          })
        });

        if (!response.ok) throw new Error("Ошибка при создании списка");

        modal.remove();
        window.location.reload();
      } catch (error) {
        console.error("Error creating list:", error);
        alert("Ошибка при создании списка");
        hideLoader();
      }
    });

    document.getElementById('delete-selected-lists').addEventListener('click', async () => {
      const checkboxes = document.querySelectorAll('.list-checkbox:checked');
      if (checkboxes.length === 0) {
        alert("Выберите списки для удаления");
        return;
      }

      showLoader();
      try {
        await Promise.all(Array.from(checkboxes).map(cb =>
          fetch('/api/lists', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
              action: 'remove',
              list_name: cb.dataset.list,
              servers: []
            })
          })
        ));
        modal.remove();
        window.location.reload();
      } catch (error) {
        console.error("Error deleting lists:", error);
        alert("Ошибка при удалении списков");
        hideLoader();
      }
    });
  }

  document.getElementById('cancel-lists').addEventListener('click', () => {
    modal.remove();
  });

  // Закрытие по клику вне модального окна
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.remove();
    }
  });
}

export async function loadListSelector() {
  try {
    const selector = document.getElementById('list-selector');
    const res = await fetch('/api/lists');
    const lists = await res.json();

    selector.innerHTML = '';
    for (const name in lists) {
      const option = document.createElement('option');
      option.value = name;
      option.textContent = name;
      selector.appendChild(option);
    }
  } catch (error) {
    console.error("Error loading lists:", error);
  }
}