const form = document.querySelector("#task-form");
const titleInput = document.querySelector("#task-title");
const submitButton = document.querySelector("#submit-button");
const cancelEditButton = document.querySelector("#cancel-edit");
const formTitle = document.querySelector("#form-title");
const message = document.querySelector("#message");
const taskList = document.querySelector("#task-list");
const summary = document.querySelector("#task-summary");
const filterButtons = document.querySelectorAll("[data-filter]");
const activityList = document.querySelector("#activity-list");
const refreshActivityButton = document.querySelector("#refresh-activity");

let tasks = [];
let filter = "all";
let editingId = null;

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) }
  });

  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
  return data;
}

function showMessage(text, type = "error") {
  message.textContent = text;
  message.classList.toggle("success", type === "success");
}

function resetForm() {
  editingId = null;
  form.reset();
  submitButton.textContent = "+ Add task";
  formTitle.textContent = "Add a task";
  cancelEditButton.classList.add("hidden");
}

async function loadTasks() {
  taskList.replaceChildren();
  const loading = document.createElement("div");
  loading.className = "empty-state";
  loading.textContent = "Loading tasks…";
  taskList.appendChild(loading);

  try {
    tasks = await api("/api/tasks");
    renderTasks();
    await loadActivity();
  } catch (error) {
    taskList.replaceChildren();
    const errorBox = document.createElement("div");
    errorBox.className = "empty-state";
    errorBox.textContent = `Could not load tasks: ${error.message} Refresh the page after checking the server and database.`;
    taskList.appendChild(errorBox);
    summary.textContent = "Connection problem";
  }
}

// CREATE and UPDATE
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = titleInput.value.trim();
  if (!title) {
    showMessage("Please enter a task title.");
    titleInput.focus();
    return;
  }

  submitButton.disabled = true;
  try {
    if (editingId) {
      await api(`/api/tasks/${encodeURIComponent(editingId)}`, {
        method: "PATCH",
        body: JSON.stringify({ title })
      });
      showMessage("Task updated.", "success");
    } else {
      await api("/api/tasks", {
        method: "POST",
        body: JSON.stringify({ title })
      });
      showMessage("Task added.", "success");
    }
    resetForm();
    await loadTasks();
  } catch (error) {
    showMessage(error.message);
  } finally {
    submitButton.disabled = false;
  }
});

cancelEditButton.addEventListener("click", () => {
  resetForm();
  showMessage("");
  titleInput.focus();
});

function startEdit(task) {
  editingId = task._id;
  titleInput.value = task.title;
  submitButton.textContent = "Save changes";
  formTitle.textContent = "Edit task";
  cancelEditButton.classList.remove("hidden");
  showMessage("Edit the title, then save your changes.", "success");
  titleInput.focus();
  titleInput.select();
}

// UPDATE completion status
async function setCompleted(task, completed) {
  try {
    await api(`/api/tasks/${encodeURIComponent(task._id)}`, {
      method: "PATCH",
      body: JSON.stringify({ completed })
    });
    await loadTasks();
  } catch (error) {
    showMessage(error.message);
    await loadTasks();
  }
}

// DELETE
async function deleteTask(task) {
  if (!window.confirm(`Delete "${task.title}"?`)) return;
  try {
    await api(`/api/tasks/${encodeURIComponent(task._id)}`, { method: "DELETE" });
    if (editingId === task._id) resetForm();
    showMessage("Task deleted.", "success");
    await loadTasks();
  } catch (error) {
    showMessage(error.message);
  }
}

// READ: safely create DOM elements without injecting task text as HTML.
async function loadActivity() {
  try {
    const activity = await api("/api/activity");
    activityList.replaceChildren();
    if (activity.length === 0) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No activity yet. Add, update, or delete a task to see the history.";
      activityList.appendChild(empty);
      return;
    }

    activity.forEach(item => {
      const row = document.createElement("div");
      row.className = "activity-row";
      const description = document.createElement("span");
      description.textContent = `${item.action[0].toUpperCase()}${item.action.slice(1)}: ${item.task_title}`;
      const time = document.createElement("time");
      time.dateTime = item.created_at;
      time.textContent = new Date(item.created_at).toLocaleString();
      row.append(description, time);
      activityList.appendChild(row);
    });
  } catch (error) {
    activityList.replaceChildren();
    const problem = document.createElement("div");
    problem.className = "empty-state";
    problem.textContent = `Could not load PostgreSQL activity: ${error.message}`;
    activityList.appendChild(problem);
  }
}

refreshActivityButton.addEventListener("click", loadActivity);

function renderTasks() {
  const visibleTasks = tasks.filter(task => {
    if (filter === "active") return !task.completed;
    if (filter === "completed") return task.completed;
    return true;
  });

  summary.textContent = `${tasks.filter(task => !task.completed).length} active · ${tasks.length} total`;
  taskList.replaceChildren();

  if (visibleTasks.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = tasks.length === 0
      ? "No tasks yet. Add your first task above."
      : "There are no tasks in this filter.";
    taskList.appendChild(empty);
    return;
  }

  visibleTasks.forEach(task => {
    const row = document.createElement("article");
    row.className = `task-row${task.completed ? " completed" : ""}`;

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.className = "task-checkbox";
    checkbox.checked = Boolean(task.completed);
    checkbox.setAttribute("aria-label", `Mark ${task.title} completed`);
    checkbox.addEventListener("change", () => setCompleted(task, checkbox.checked));

    const title = document.createElement("span");
    title.className = "task-title-text";
    title.textContent = task.title;

    const actions = document.createElement("div");
    actions.className = "task-actions";

    const editButton = document.createElement("button");
    editButton.type = "button";
    editButton.className = "button secondary";
    editButton.textContent = "Edit";
    editButton.addEventListener("click", () => startEdit(task));

    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "button danger";
    deleteButton.textContent = "Delete";
    deleteButton.addEventListener("click", () => deleteTask(task));

    actions.append(editButton, deleteButton);
    row.append(checkbox, title, actions);
    taskList.appendChild(row);
  });
}

filterButtons.forEach(button => {
  button.addEventListener("click", () => {
    filter = button.dataset.filter;
    filterButtons.forEach(item => item.classList.toggle("active", item === button));
    renderTasks();
  });
});

loadTasks();
