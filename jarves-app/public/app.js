const chatWindow = document.getElementById("chatWindow");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const taskForm = document.getElementById("taskForm");
const taskTitle = document.getElementById("taskTitle");
const taskList = document.getElementById("taskList");

const renderMessage = (speaker, text) => {
  const item = document.createElement("div");
  item.className = "message";
  item.innerHTML = `<strong>${speaker}</strong><div>${text.replace(/\n/g, "<br />")}</div>`;
  chatWindow.appendChild(item);
  chatWindow.scrollTop = chatWindow.scrollHeight;
};

const loadTasks = async () => {
  const response = await fetch("/api/tasks");
  const data = await response.json();
  taskList.innerHTML = "";
  data.tasks.forEach((task) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${task.title}</span><button data-id="${task.id}">Delete</button>`;
    taskList.appendChild(li);
  });
};

const addTask = async (title) => {
  const response = await fetch("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title })
  });
  if (response.ok) {
    await loadTasks();
    taskTitle.value = "";
  }
};

const deleteTask = async (id) => {
  const response = await fetch(`/api/tasks/${id}`, { method: "DELETE" });
  if (response.ok) {
    await loadTasks();
  }
};

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;
  renderMessage("You", text);
  chatInput.value = "";

  const response = await fetch("/api/jarves", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text })
  });

  const data = await response.json();
  if (response.ok) {
    renderMessage("Jarves", data.reply);
  } else {
    renderMessage("Jarves", data.error || "An error occurred.");
  }
});

taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = taskTitle.value.trim();
  if (!title) return;
  await addTask(title);
});

taskList.addEventListener("click", async (event) => {
  if (event.target.tagName === "BUTTON") {
    const id = event.target.dataset.id;
    await deleteTask(id);
  }
});

loadTasks().catch(console.error);
