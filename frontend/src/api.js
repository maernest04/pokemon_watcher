const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/_/backend"
const TOKEN_KEY = "pokemon_watcher_token"

export function getToken() {
  return window.localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  if (!token) {
    window.localStorage.removeItem(TOKEN_KEY)
    return
  }
  window.localStorage.setItem(TOKEN_KEY, token)
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = new Headers(options.headers || {})
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json")
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })
  if (response.status === 204) {
    return null
  }
  const contentType = response.headers.get("content-type") || ""
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text()
  if (!response.ok) {
    let detail = "Request failed"
    if (typeof data === "object" && data !== null && data.detail) {
      if (Array.isArray(data.detail)) {
        // Handle FastAPI validation errors (422)
        detail = data.detail.map((err) => `${err.loc.join(".")}: ${err.msg}`).join(", ")
      } else {
        detail = data.detail
      }
    }
    throw new Error(detail)
  }
  return data
}

export function register(payload) {
  return request("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function login(payload) {
  return request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function getMe() {
  return request("/api/users/me")
}

export function updateMe(payload) {
  return request("/api/users/me", {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
}

export function listSearches() {
  return request("/api/searches/")
}

export function createSearch(payload) {
  return request("/api/searches", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function updateSearch(searchId, payload) {
  return request(`/api/searches/${searchId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
}

export function deleteSearch(searchId) {
  return request(`/api/searches/${searchId}`, {
    method: "DELETE",
  })
}

export function listAlerts() {
  return request("/api/alerts/")
}

export function refreshMarketPrice(searchId) {
  return request(`/api/searches/${searchId}/refresh-market`, {
    method: "POST",
  })
}

export function testDiscord() {
  return request("/api/test/discord", {
    method: "POST",
  })
}

export function testEbay(payload) {
  return request("/api/test/ebay", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function testPokedata(payload) {
  return request("/api/test/pokedata", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}
export function adminListUsers() {
  return request("/api/users/admin/users")
}

export function adminApproveUser(userId) {
  return request(`/api/users/admin/users/${userId}/approve`, {
    method: "POST",
  })
}

export function adminUnapproveUser(userId) {
  return request(`/api/users/admin/users/${userId}/unapprove`, {
    method: "POST",
  })
}

export function adminToggleAdmin(userId) {
  return request(`/api/users/admin/users/${userId}/toggle-admin`, {
    method: "POST",
  })
}

export function adminDeleteUser(userId) {
  return request(`/api/users/admin/users/${userId}`, {
    method: "DELETE",
  })
}

export function adminToggleSearch(userId, searchId) {
  return request(`/api/users/admin/users/${userId}/searches/${searchId}/toggle`, {
    method: "POST",
  })
}

export function adminDeleteSearch(userId, searchId) {
  return request(`/api/users/admin/users/${userId}/searches/${searchId}`, {
    method: "DELETE",
  })
}
