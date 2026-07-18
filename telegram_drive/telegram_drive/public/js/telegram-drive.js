const call = async (method, body) => {
  const options = body instanceof FormData
    ? { method: "POST", body }
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) };
  const response = await fetch(`/api/method/${method}`, options);
  const data = await response.json();
  if (!response.ok || data.exc) throw new Error(data.message || data.exc || "Request failed");
  return data.message;
};

const render = async () => {
  const [settings, files, folders] = await Promise.all([
    call("telegram_drive.api.settings.get_settings"),
    call("telegram_drive.api.files.list"),
    call("telegram_drive.api.folders.list"),
  ]);
  document.querySelector("h1").textContent = settings.drive_name || "Telegram Drive";
  document.querySelector("#status").textContent = "Connected to Frappe metadata APIs";
  document.querySelector("#files").innerHTML = files.map(file => `
    <div class="row">
      <div><strong>${file.name}</strong><div class="muted">${file.size || 0} bytes</div></div>
      <a href="/api/method/telegram_drive.api.files.download?file_id=${encodeURIComponent(file.id)}">Download</a>
    </div>`).join("") || `<div class="muted">No files yet.</div>`;
  document.querySelector("#folders").innerHTML = folders.map(folder => `
    <div class="row"><strong>${folder.name}</strong><span class="muted">${folder.id}</span></div>`).join("") || `<div class="muted">No folders yet.</div>`;
};

document.querySelector("#refresh").addEventListener("click", render);
document.querySelector("#folder-form").addEventListener("submit", async event => {
  event.preventDefault();
  await call("telegram_drive.api.folders.create", { folder_name: document.querySelector("#folder-name").value });
  event.target.reset();
  render();
});
document.querySelector("#upload-form").addEventListener("submit", async event => {
  event.preventDefault();
  const form = new FormData();
  form.append("file", document.querySelector("#file").files[0]);
  await call("telegram_drive.api.files.upload", form);
  event.target.reset();
  document.querySelector("#status").textContent = "Upload queued. Refresh after the worker completes.";
});

render().catch(error => {
  document.querySelector("#status").textContent = error.message;
});
