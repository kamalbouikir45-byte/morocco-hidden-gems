/* ===========================================================
   Maroc Authentique — Admin dashboard logic
   Talks to the same Flask + MySQL backend as the public site.
   Endpoints used:
     GET    /api/villages?search=&type=
     POST   /api/villages
     PUT    /api/villages/:id
     DELETE /api/villages/:id
     GET    /api/reservations
     DELETE /api/reservations/:id
     GET    /api/stats
=========================================================== */

// When opened directly via file:// fall back to a local Flask server.
const API_BASE =
  location.protocol === "file:" ? "http://localhost:5000" : "";

const TYPE_COLORS = {
  Montagne: "#15512f",
  Désert: "#d98a2b",
  Culturel: "#1d7fb8",
  Naturel: "#6fae57",
};
const MONTHS = [
  "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
  "Juil", "Août", "Sep", "Oct", "Nov", "Déc",
];

let villagesCache = [];
let typeChart = null;
let monthlyChart = null;
let modal = null;

/* ---------- Helpers ---------- */
async function api(path, options = {}) {
  const res = await fetch(API_BASE + path, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Erreur serveur");
  return data;
}

function escapeHtml(str) {
  return String(str ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function showModalMessage(text, type) {
  const el = document.getElementById("modalMessage");
  el.textContent = text;
  el.className = `form-message ${type}`;
}

/* ---------- Attractions ---------- */
async function loadAttractions() {
  const search = document.getElementById("searchInput").value.trim();
  const type = document.getElementById("typeFilter").value;
  const body = document.getElementById("attractionsBody");

  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (type) params.set("type", type);

  try {
    const rows = await api("/api/villages?" + params.toString());
    villagesCache = rows;
    if (!rows.length) {
      body.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">Aucune attraction</td></tr>`;
      return;
    }
    body.innerHTML = rows
      .map(
        (v) => `
        <tr>
          <td class="fw-semibold">${escapeHtml(v.name)}</td>
          <td><span class="type-pill" style="--pill:${TYPE_COLORS[v.type] || "#777"}">${escapeHtml(v.type)}</span></td>
          <td>${escapeHtml(v.region)}</td>
          <td>${v.price != null ? Math.round(v.price) : "—"}</td>
          <td class="text-end text-nowrap">
            <button class="icon-btn" data-edit="${v.id}" title="Modifier"><i class="bi bi-pencil"></i></button>
            <button class="icon-btn icon-btn-danger" data-del="${v.id}" title="Supprimer"><i class="bi bi-trash"></i></button>
          </td>
        </tr>`
      )
      .join("");
  } catch (e) {
    body.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-4">${escapeHtml(e.message)}</td></tr>`;
  }
}

/* ---------- Reservations ---------- */
async function loadReservations() {
  const body = document.getElementById("reservationsBody");
  try {
    const rows = await api("/api/reservations");
    if (!rows.length) {
      body.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">Aucune réservation</td></tr>`;
      return;
    }
    body.innerHTML = rows
      .map(
        (r) => `
        <tr>
          <td class="fw-semibold">${escapeHtml(r.name)}</td>
          <td>${escapeHtml(r.place)}</td>
          <td>${escapeHtml((r.visit_date || "").slice(0, 10))}</td>
          <td>${escapeHtml(r.visitor_type)}</td>
          <td class="text-end">
            <button class="icon-btn icon-btn-danger" data-delres="${r.id}" title="Supprimer"><i class="bi bi-trash"></i></button>
          </td>
        </tr>`
      )
      .join("");
  } catch (e) {
    body.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-4">${escapeHtml(e.message)}</td></tr>`;
  }
}

/* ---------- Statistics ---------- */
async function loadStats() {
  try {
    const stats = await api("/api/stats");
    document.getElementById("countVillages").textContent = stats.total_villages;
    document.getElementById("countReservations").textContent = stats.total_reservations;

    const labels = Object.keys(stats.by_type);
    const values = Object.values(stats.by_type);
    const colors = labels.map((l) => TYPE_COLORS[l] || "#999");

    if (typeChart) typeChart.destroy();
    typeChart = new Chart(document.getElementById("typeChart"), {
      type: "doughnut",
      data: { labels, datasets: [{ data: values, backgroundColor: colors, borderWidth: 0 }] },
      options: {
        plugins: { legend: { position: "bottom", labels: { font: { family: "Inter" } } } },
      },
    });

    if (monthlyChart) monthlyChart.destroy();
    monthlyChart = new Chart(document.getElementById("monthlyChart"), {
      type: "line",
      data: {
        labels: MONTHS,
        datasets: [
          {
            label: "Réservations",
            data: stats.monthly,
            borderColor: "#15512f",
            backgroundColor: "rgba(21,81,47,0.12)",
            fill: true,
            tension: 0.35,
            pointBackgroundColor: "#d98a2b",
          },
        ],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      },
    });
  } catch (e) {
    console.log("[v0] stats error:", e.message);
  }
}

/* ---------- Modal: add / edit ---------- */
function openAddModal() {
  document.getElementById("attractionForm").reset();
  document.getElementById("attractionId").value = "";
  document.getElementById("attractionModalTitle").textContent = "Ajouter une attraction";
  document.getElementById("modalMessage").className = "form-message d-none";
  modal.show();
}

function openEditModal(id) {
  const v = villagesCache.find((x) => String(x.id) === String(id));
  if (!v) return;
  document.getElementById("attractionId").value = v.id;
  document.getElementById("fName").value = v.name;
  document.getElementById("fRegion").value = v.region;
  document.getElementById("fType").value = v.type;
  document.getElementById("fPrice").value = v.price != null ? Math.round(v.price) : 0;
  document.getElementById("fImage").value = v.image || "";
  document.getElementById("fDescription").value = v.description || "";
  document.getElementById("attractionModalTitle").textContent = "Modifier l'attraction";
  document.getElementById("modalMessage").className = "form-message d-none";
  modal.show();
}

async function submitAttraction(e) {
  e.preventDefault();
  const id = document.getElementById("attractionId").value;
  const payload = {
    name: document.getElementById("fName").value.trim(),
    region: document.getElementById("fRegion").value.trim(),
    type: document.getElementById("fType").value,
    price: document.getElementById("fPrice").value,
    image: document.getElementById("fImage").value.trim(),
    description: document.getElementById("fDescription").value.trim(),
  };
  try {
    if (id) {
      await api(`/api/villages/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    } else {
      await api("/api/villages", { method: "POST", body: JSON.stringify(payload) });
    }
    modal.hide();
    await Promise.all([loadAttractions(), loadStats()]);
  } catch (err) {
    showModalMessage(err.message, "error");
  }
}

async function deleteAttraction(id) {
  if (!confirm("Supprimer cette attraction ?")) return;
  try {
    await api(`/api/villages/${id}`, { method: "DELETE" });
    await Promise.all([loadAttractions(), loadStats()]);
  } catch (e) {
    alert(e.message);
  }
}

async function deleteReservation(id) {
  if (!confirm("Supprimer cette réservation ?")) return;
  try {
    await api(`/api/reservations/${id}`, { method: "DELETE" });
    await Promise.all([loadReservations(), loadStats()]);
  } catch (e) {
    alert(e.message);
  }
}

/* ---------- PDF export ---------- */
function exportPDF() {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();
  doc.setFontSize(16);
  doc.text("Office du Tourisme Marocain — Attractions", 14, 18);
  doc.setFontSize(10);
  doc.text(new Date().toLocaleString("fr-FR"), 14, 25);
  doc.autoTable({
    startY: 30,
    head: [["Nom", "Type", "Région", "Prix (MAD)"]],
    body: villagesCache.map((v) => [v.name, v.type, v.region, v.price != null ? Math.round(v.price) : "—"]),
    headStyles: { fillColor: [21, 81, 47] },
    styles: { font: "helvetica", fontSize: 9 },
  });
  doc.save("attractions-maroc.pdf");
}

/* ---------- Navigation / misc ---------- */
function setupNav() {
  document.querySelectorAll("[data-nav]").forEach((link) => {
    link.addEventListener("click", () => {
      document.querySelectorAll("[data-nav]").forEach((l) => l.classList.remove("active"));
      link.classList.add("active");
      document.getElementById("adminSidebar").classList.remove("open");
    });
  });
  document.getElementById("menuToggle").addEventListener("click", () => {
    document.getElementById("adminSidebar").classList.toggle("open");
  });
}

/* ---------- Init ---------- */
document.addEventListener("DOMContentLoaded", () => {
  modal = new bootstrap.Modal(document.getElementById("attractionModal"));

  document.getElementById("refreshBtn").addEventListener("click", refreshAll);
  document.getElementById("searchInput").addEventListener("input", debounce(loadAttractions, 300));
  document.getElementById("typeFilter").addEventListener("change", loadAttractions);
  document.getElementById("addBtn").addEventListener("click", openAddModal);
  document.getElementById("statsBtn").addEventListener("click", () =>
    document.getElementById("section-stats").scrollIntoView({ behavior: "smooth" })
  );
  document.getElementById("exportBtn").addEventListener("click", exportPDF);
  document.getElementById("attractionForm").addEventListener("submit", submitAttraction);

  // Event delegation for table action buttons
  document.getElementById("attractionsBody").addEventListener("click", (e) => {
    const edit = e.target.closest("[data-edit]");
    const del = e.target.closest("[data-del]");
    if (edit) openEditModal(edit.dataset.edit);
    if (del) deleteAttraction(del.dataset.del);
  });
  document.getElementById("reservationsBody").addEventListener("click", (e) => {
    const del = e.target.closest("[data-delres]");
    if (del) deleteReservation(del.dataset.delres);
  });

  setupNav();
  refreshAll();
});

function refreshAll() {
  loadAttractions();
  loadReservations();
  loadStats();
}

function debounce(fn, wait) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(null, args), wait);
  };
}
