const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
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
    const detail =
      typeof data === "object" && data !== null && "detail" in data
        ? data.detail
        : "Request failed"
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
