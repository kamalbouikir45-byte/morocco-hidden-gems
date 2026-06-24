/* ===========================================================
   Maroc Authentique — Frontend logic
   - Loads villages from the Flask API (falls back to local data)
   - Search + type filtering
   - Populates the reservation "Lieu" dropdown
   - Submits reservations to the Flask API
=========================================================== */

// Base URL of the Flask backend. Empty string = same origin.
const API_BASE = "https://morocco-hidden-gems-94zz.onrender.com";
fetch(`${API_BASE}/api/villages`)
fetch(`${API_BASE}/api/reservations`)
// Fallback data so the page still works if the backend isn't running.
const FALLBACK_VILLAGES = [
  {
    id: 1,
    name: "Vallée d'Aït Bouguemez",
    region: "Haut Atlas",
    type: "Montagne",
    description: "La « vallée heureuse » : terrasses verdoyantes, villages de pisé et hospitalité berbère.",
    price: 450,
    image: "static/images/village-aitbouguemez.png",
  },
  {
    id: 2,
    name: "Dunes de Tinfou",
    region: "Drâa-Tafilalet",
    type: "Désert",
    description: "Des dunes dorées loin de la foule de Merzouga, idéales pour une nuit sous les étoiles.",
    price: 600,
    image: "static/images/village-desert.png",
  },
  {
    id: 3,
    name: "Cascades d'Akchour",
    region: "Rif",
    type: "Naturel",
    description: "Bassins turquoise et pont naturel de Dieu au cœur du parc de Talassemtane.",
    price: 300,
    image: "static/images/village-cascade.png",
  },
  {
    id: 4,
    name: "Lac d'Imilchil",
    region: "Haut Atlas",
    type: "Culturel",
    description: "Lacs d'altitude et célèbre moussem des fiançailles des Aït Haddidou.",
    price: 520,
    image: "static/images/village-imilchil.png",
  },
  {
    id: 5,
    name: "Kasbah de Tamnougalt",
    region: "Vallée du Drâa",
    type: "Culturel",
    description: "Ancienne kasbah de terre ocre entourée d'une palmeraie luxuriante.",
    price: 380,
    image: "static/images/village-kasbah.png",
  },
  {
    id: 6,
    name: "Village bleu de Chefchaouen",
    region: "Rif",
    type: "Naturel",
    description: "Ruelles bleues hors des circuits touristiques, ateliers d'artisans et calme montagnard.",
    price: 340,
    image: "static/images/village-bluevillage.png",
  },
];

let allVillages = [];

const grid = document.getElementById("villagesGrid");
const noResults = document.getElementById("noResults");
const searchInput = document.getElementById("searchInput");
const typeFilter = document.getElementById("typeFilter");
const placeSelect = document.getElementById("place");
const form = document.getElementById("reservationForm");
const formMessage = document.getElementById("formMessage");

/* ---------- Load villages ---------- */
async function loadVillages() {
  try {
    const res = await fetch(`${API_BASE}/api/villages`);
    if (!res.ok) throw new Error("API error");
    const data = await res.json();
    allVillages = Array.isArray(data) && data.length ? data : FALLBACK_VILLAGES;
  } catch (err) {
    console.log("[v0] Backend unavailable, using fallback data:", err.message);
    allVillages = FALLBACK_VILLAGES;
  }
  populatePlaceOptions();
  renderVillages();
}

/* ---------- Render village cards ---------- */
function renderVillages() {
  const query = searchInput.value.trim().toLowerCase();
  const type = typeFilter.value;

  const filtered = allVillages.filter((v) => {
    const matchesQuery =
      !query ||
      v.name.toLowerCase().includes(query) ||
      v.region.toLowerCase().includes(query) ||
      v.description.toLowerCase().includes(query);
    const matchesType = !type || v.type === type;
    return matchesQuery && matchesType;
  });

  grid.innerHTML = "";

  if (filtered.length === 0) {
    noResults.hidden = false;
    return;
  }
  noResults.hidden = true;

  filtered.forEach((v) => {
    const col = document.createElement("div");
    col.className = "col-12 col-sm-6 col-lg-4";
    col.innerHTML = `
      <article class="village-card">
        <div class="village-img" style="background-image:url('${v.image}')">
          <span class="village-badge">${v.type}</span>
        </div>
        <div class="village-body">
          <span class="village-region">${v.region}</span>
          <h3 class="village-name">${v.name}</h3>
          <p class="village-desc">${v.description}</p>
          <div class="village-foot">
            <span class="village-price">${v.price} MAD <small>/ pers.</small></span>
            <button type="button" class="village-reserve" data-name="${v.name}">Réserver →</button>
          </div>
        </div>
      </article>`;
    grid.appendChild(col);
  });

  // Wire up the "Réserver" buttons on each card
  grid.querySelectorAll(".village-reserve").forEach((btn) => {
    btn.addEventListener("click", () => {
      placeSelect.value = btn.dataset.name;
      document.getElementById("reservation").scrollIntoView({ behavior: "smooth" });
    });
  });
}

/* ---------- Populate reservation dropdown ---------- */
function populatePlaceOptions() {
  placeSelect.innerHTML = '<option value="">Choisir un lieu</option>';
  allVillages.forEach((v) => {
    const opt = document.createElement("option");
    opt.value = v.name;
    opt.textContent = v.name;
    placeSelect.appendChild(opt);
  });
}

/* ---------- Filters ---------- */
searchInput.addEventListener("input", renderVillages);
typeFilter.addEventListener("change", renderVillages);

/* ---------- Reservation form ---------- */
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  formMessage.hidden = true;
  formMessage.className = "form-message";

  const payload = {
    visitor_type: form.visitorType.value,
    name: form.name.value.trim(),
    email: form.email.value.trim(),
    date: form.date.value,
    place: form.place.value,
  };

  // Basic validation
  if (!payload.name || !payload.email || !payload.date || !payload.place) {
    showMessage("Veuillez remplir tous les champs.", "error");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/reservations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (res.ok) {
      showMessage(
        `Merci ${payload.name} ! Votre réservation pour « ${payload.place} » a bien été enregistrée.`,
        "success"
      );
      form.reset();
    } else {
      showMessage(data.error || "Une erreur est survenue.", "error");
    }
  } catch (err) {
    console.log("[v0] Reservation submit failed:", err.message);
    showMessage(
      "Impossible de contacter le serveur. Vérifiez que le backend Flask est démarré.",
      "error"
    );
  }
});

function showMessage(text, type) {
  formMessage.textContent = text;
  formMessage.className = `form-message ${type}`;
  formMessage.hidden = false;
}

/* ---------- Init ---------- */
loadVillages();
