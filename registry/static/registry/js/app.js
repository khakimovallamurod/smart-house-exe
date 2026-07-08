const sidebar = document.getElementById("sidebar");
document.querySelectorAll("[data-sidebar-open]").forEach((button) => button.addEventListener("click", () => sidebar.classList.remove("-translate-x-full")));
document.querySelectorAll("[data-sidebar-close]").forEach((button) => button.addEventListener("click", () => sidebar.classList.add("-translate-x-full")));

setTimeout(() => document.getElementById("toasts")?.remove(), 4200);
document.addEventListener("submit", (event) => {
  const form = event.target.closest("[data-confirm]");
  if (form && !confirm(form.dataset.confirm)) event.preventDefault();
  const swalForm = event.target.closest("[data-swal-delete]");
  if (swalForm) {
    event.preventDefault();
    openSwalConfirm(swalForm.dataset.swalDelete, () => swalForm.submit());
  }
});

function closeModal() {
  document.getElementById("modal-root").innerHTML = "";
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeModal();
});

document.addEventListener("click", async (event) => {
  const localOpen = event.target.closest("[data-open-local-modal]");
  if (localOpen) {
    document.getElementById(localOpen.dataset.openLocalModal)?.classList.remove("hidden");
    return;
  }
  if (event.target.matches("[data-close-local-modal]") || event.target.closest("[data-close-local-modal]")) {
    event.target.closest(".local-modal")?.classList.add("hidden");
    return;
  }
  if (event.target.classList.contains("local-modal")) {
    event.target.classList.add("hidden");
    return;
  }
  const addResidentRow = event.target.closest("[data-add-resident-row]");
  if (addResidentRow) {
    const wrapper = document.getElementById("multi-residents");
    const first = wrapper.querySelector(".resident-fieldset");
    const clone = first.cloneNode(true);
    const index = wrapper.querySelectorAll(".resident-fieldset").length;
    clone.querySelectorAll("input, textarea").forEach((field) => {
      if (field.type === "checkbox") {
        field.checked = false;
        field.value = index;
      } else {
        field.value = "";
      }
    });
    clone.querySelectorAll("select").forEach((field) => field.selectedIndex = 0);
    wrapper.appendChild(clone);
    return;
  }
  const roomButton = event.target.closest("[data-modal-url]");
  if (roomButton) {
    const root = document.getElementById("modal-root");
    root.innerHTML = '<div class="modal-backdrop"><div class="rounded bg-white p-6">Yuklanmoqda...</div></div>';
    const response = await fetch(roomButton.dataset.modalUrl);
    root.innerHTML = await response.text();
    return;
  }
  const renderComplaintsButton = event.target.closest("[data-render-complaints]");
  if (renderComplaintsButton) {
    renderComplaintNotes();
    return;
  }
  const residentSwitch = event.target.closest("[data-resident-target]");
  if (residentSwitch) {
    const modal = residentSwitch.closest(".modal-panel");
    modal.querySelectorAll(".resident-switch").forEach((button) => button.classList.remove("active"));
    modal.querySelectorAll(".resident-detail").forEach((section) => section.classList.add("hidden"));
    residentSwitch.classList.add("active");
    modal.querySelector(`#${residentSwitch.dataset.residentTarget}`)?.classList.remove("hidden");
    return;
  }
  if (event.target.matches("[data-modal-close]") || event.target.closest("[data-modal-close]")) closeModal();
  if (event.target.matches("[data-modal-backdrop]")) closeModal();

  const addResident = event.target.closest('[data-add-form="resident"]');
  if (addResident) {
    const totalInput = document.querySelector("#id_resident-TOTAL_FORMS");
    const template = document.querySelector("#resident-empty-form").innerHTML;
    const index = Number(totalInput.value);
    document.querySelector("#resident-forms").insertAdjacentHTML("beforeend", template.replaceAll("__prefix__", index));
    totalInput.value = index + 1;
  }

  const addRelated = event.target.closest("[data-add-related]");
  if (addRelated) {
    const residentId = addRelated.dataset.addRelated;
    const totalInput = document.querySelector(`#id_related-${residentId}-TOTAL_FORMS`);
    const template = document.querySelector(`#related-empty-${residentId}`).innerHTML;
    const index = Number(totalInput.value);
    document.querySelector(`#related-${residentId}`).insertAdjacentHTML("beforeend", template.replaceAll("__prefix__", index));
    totalInput.value = index + 1;
  }
});

function openSwalConfirm(message, onConfirm) {
  const existing = document.getElementById("swal-confirm");
  if (existing) existing.remove();
  const shell = document.createElement("div");
  shell.id = "swal-confirm";
  shell.className = "swal-backdrop";
  shell.innerHTML = `
    <div class="swal-panel">
      <div class="swal-icon"><i class="bi bi-exclamation-triangle"></i></div>
      <h3>O'chirishni tasdiqlang</h3>
      <p>${message}</p>
      <div class="swal-actions">
        <button class="btn-secondary" type="button" data-swal-cancel>Bekor qilish</button>
        <button class="btn-danger" type="button" data-swal-confirm>O'chirish</button>
      </div>
    </div>
  `;
  document.body.appendChild(shell);
  shell.querySelector("[data-swal-cancel]").addEventListener("click", () => shell.remove());
  shell.querySelector("[data-swal-confirm]").addEventListener("click", () => {
    shell.remove();
    onConfirm();
  });
}

async function drawCharts() {
  const pie = document.getElementById("pieChart");
  if (pie) {
    const data = await fetch("/api/stats/").then((response) => response.json());
    drawPie(pie, data.pie, ["#047857", "#be123c"]);
    drawLine(document.getElementById("lineChart"), data.line, "#3E6AE1");
    drawBar(document.getElementById("barChart"), data.bar, data.bar_labels, ["#171A20", "#047857", "#be123c", "#3E6AE1"]);
  }
  const entranceRisk = document.getElementById("entranceRiskChart");
  if (entranceRisk) {
    const values = JSON.parse(entranceRisk.dataset.values || "[]");
    drawLine(entranceRisk, values.length === 1 ? [0, values[0]] : values, "#be123c", entranceRisk.dataset.labelPrefix || "");
  }
}

function drawPie(canvas, values, colors) {
  const ctx = canvas.getContext("2d");
  const total = values.reduce((sum, value) => sum + value, 0) || 1;
  let start = -Math.PI / 2;
  values.forEach((value, index) => {
    const angle = (value / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(150, 95);
    ctx.arc(150, 95, 74, start, start + angle);
    ctx.fillStyle = colors[index];
    ctx.fill();
    start += angle;
  });
}

function drawLine(canvas, values, color, labelPrefix = "") {
  const ctx = canvas.getContext("2d");
  const width = canvas.width = canvas.offsetWidth;
  const cssHeight = Number.parseInt(getComputedStyle(canvas).height, 10);
  const height = canvas.height = cssHeight || Number(canvas.getAttribute("height")) || 190;
  const max = Math.max(...values, 1);
  const bottomPad = labelPrefix ? 18 : 20;
  const topPad = 16;
  const chartHeight = Math.max(48, height - topPad - bottomPad);
  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "#e5e7eb";
  ctx.lineWidth = 1;
  for (let step = 0; step < 4; step += 1) {
    const y = topPad + step * (chartHeight / 3);
    ctx.beginPath();
    ctx.moveTo(20, y);
    ctx.lineTo(width - 20, y);
    ctx.stroke();
  }
  ctx.strokeStyle = color;
  ctx.lineWidth = 3;
  ctx.beginPath();
  (values.length ? values : [0]).forEach((value, index, arr) => {
    const x = 20 + index * ((width - 40) / Math.max(arr.length - 1, 1));
    const y = height - bottomPad - (value / max) * chartHeight;
    index ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  });
  ctx.stroke();
  (values.length ? values : [0]).forEach((value, index, arr) => {
    const x = 20 + index * ((width - 40) / Math.max(arr.length - 1, 1));
    const y = height - bottomPad - (value / max) * chartHeight;
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    if (labelPrefix) {
      ctx.fillStyle = "#5C5E62";
      ctx.font = "12px Arial";
      ctx.textAlign = "center";
      ctx.fillText(`${labelPrefix}${index + 1}`, x, height - 4);
      ctx.fillStyle = "#171A20";
      ctx.font = "600 12px Arial";
      ctx.fillText(String(value), x, Math.max(14, y - 8));
    }
  });
}

function drawBar(canvas, values, labels, colors) {
  const ctx = canvas.getContext("2d");
  const width = canvas.width = canvas.offsetWidth;
  const height = canvas.height = 190;
  const max = Math.max(...values, 1);
  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "#e5e7eb";
  ctx.beginPath();
  ctx.moveTo(18, height - 28);
  ctx.lineTo(width - 12, height - 28);
  ctx.stroke();
  const gap = 14;
  const innerWidth = width - 44;
  const barWidth = Math.max(24, (innerWidth - gap * (values.length - 1)) / values.length);
  values.forEach((value, index) => {
    const barHeight = value ? Math.max(8, (value / max) * 124) : 0;
    const x = 24 + index * (barWidth + gap);
    const y = height - barHeight - 30;
    ctx.fillStyle = colors[index];
    ctx.fillRect(x, y, barWidth, barHeight);
    ctx.fillStyle = "#171A20";
    ctx.font = "600 12px Arial";
    ctx.textAlign = "center";
    ctx.fillText(String(value), x + barWidth / 2, Math.max(14, y - 6));
    ctx.fillStyle = "#5C5E62";
    ctx.font = "12px Arial";
    ctx.fillText(labels[index] || "", x + barWidth / 2, height - 8);
  });
}

drawCharts();

function syncConditionalFields() {
  document.querySelectorAll("[data-conditional-for]").forEach((section) => {
    const fieldName = section.dataset.conditionalFor;
    const checked = document.querySelector(`input[name="${fieldName}"]:checked`);
    const expectedValue = section.dataset.conditionalValue;
    const isActive = checked && (
      expectedValue ? checked.value === expectedValue : (checked.value === "True" || checked.value === "true" || checked.value === "1")
    );
    section.classList.toggle("hidden", !isActive);
    section.querySelectorAll("input, textarea, select").forEach((field) => {
      field.disabled = !isActive;
    });
  });
  document.querySelectorAll("[data-conditional-for].hidden").forEach((section) => {
    section.querySelectorAll("input, textarea, select").forEach((field) => {
      field.disabled = true;
    });
  });
}

document.addEventListener("change", (event) => {
  if (event.target.matches('input[type="radio"]')) {
    syncConditionalFields();
  }
  if (event.target.matches(".file-picker input[type='file']")) {
    const label = event.target.closest(".file-picker").querySelector("[data-file-name]");
    label.textContent = event.target.files?.[0]?.name || "Rasm tanlash";
  }
});

syncConditionalFields();

function renderComplaintNotes() {
  const container = document.getElementById("complaint-notes");
  const countInput = document.querySelector('input[name="complaint_count"]');
  if (!container || !countInput || countInput.disabled) return;
  let existing = [];
  try {
    existing = JSON.parse(container.dataset.existing || "[]");
  } catch (_) {
    existing = [];
  }
  const count = Math.max(0, Number(countInput.value || 0));
  container.innerHTML = "";
  for (let index = 0; index < count; index += 1) {
    const label = document.createElement("label");
    label.innerHTML = `
      <span class="label">${index + 1}-murojaat izohi</span>
      <textarea class="form-input" name="complaint_notes" rows="2" placeholder="Murojaat mazmunini yozing">${existing[index] || ""}</textarea>
    `;
    container.appendChild(label);
  }
}

const complaintNotesContainer = document.getElementById("complaint-notes");
if (complaintNotesContainer) {
  try {
    if (JSON.parse(complaintNotesContainer.dataset.existing || "[]").length) renderComplaintNotes();
  } catch (_) {
    // Existing notes are optional.
  }
}
