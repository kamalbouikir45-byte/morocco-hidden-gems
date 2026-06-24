/* ===========================================================
   Maroc Authentique — Auth page logic
   Handles tab switching, login and registration via the Flask API.
=========================================================== */

const API_BASE = ""; // same origin as the Flask server

const tabLogin = document.getElementById("tab-login");
const tabRegister = document.getElementById("tab-register");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");

/* ---------- Tab switching ---------- */
function showLogin() {
  tabLogin.classList.add("active");
  tabLogin.setAttribute("aria-selected", "true");
  tabRegister.classList.remove("active");
  tabRegister.setAttribute("aria-selected", "false");
  loginForm.classList.remove("d-none");
  registerForm.classList.add("d-none");
}

function showRegister() {
  tabRegister.classList.add("active");
  tabRegister.setAttribute("aria-selected", "true");
  tabLogin.classList.remove("active");
  tabLogin.setAttribute("aria-selected", "false");
  registerForm.classList.remove("d-none");
  loginForm.classList.add("d-none");
}

tabLogin.addEventListener("click", showLogin);
tabRegister.addEventListener("click", showRegister);

/* ---------- Helpers ---------- */
function showMessage(el, text, type) {
  el.textContent = text;
  el.classList.remove("d-none", "success", "error");
  el.classList.add(type);
}

async function postJSON(url, body) {
  const res = await fetch(API_BASE + url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include", // keep the session cookie
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

/* ---------- Login ---------- */
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = document.getElementById("login-message");
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;

  if (!email || !password) {
    showMessage(msg, "Veuillez remplir tous les champs.", "error");
    return;
  }

  const btn = loginForm.querySelector("button[type=submit]");
  btn.disabled = true;
  btn.textContent = "Connexion…";

  try {
    const { ok, data } = await postJSON("/api/login", { email, password });
    if (ok) {
      showMessage(msg, "Connexion réussie ! Redirection…", "success");
      setTimeout(() => (window.location.href = "index.html"), 900);
    } else {
      showMessage(msg, data.error || "Email ou mot de passe incorrect.", "error");
    }
  } catch (err) {
    showMessage(msg, "Le serveur est injoignable. Réessayez plus tard.", "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Se connecter";
  }
});

/* ---------- Register ---------- */
registerForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = document.getElementById("register-message");
  const name = document.getElementById("register-name").value.trim();
  const email = document.getElementById("register-email").value.trim();
  const password = document.getElementById("register-password").value;

  if (!name || !email || !password) {
    showMessage(msg, "Veuillez remplir tous les champs.", "error");
    return;
  }
  if (password.length < 6) {
    showMessage(msg, "Le mot de passe doit contenir au moins 6 caractères.", "error");
    return;
  }

  const btn = registerForm.querySelector("button[type=submit]");
  btn.disabled = true;
  btn.textContent = "Création…";

  try {
    const { ok, data } = await postJSON("/api/register", { name, email, password });
    if (ok) {
      showMessage(msg, "Compte créé ! Redirection…", "success");
      setTimeout(() => (window.location.href = "index.html"), 900);
    } else {
      showMessage(msg, data.error || "Impossible de créer le compte.", "error");
    }
  } catch (err) {
    showMessage(msg, "Le serveur est injoignable. Réessayez plus tard.", "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Créer mon compte";
  }
});
