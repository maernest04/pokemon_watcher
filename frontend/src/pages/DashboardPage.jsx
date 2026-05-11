import { useEffect, useMemo, useState } from "react"
import {
  createSearch,
  deleteSearch,
  listAlerts,
  listSearches,
  refreshMarketPrice,
  testDiscord,
  testEbay,
  testPokedata,
  updateMe,
  updateSearch,
  adminListUsers,
  adminApproveUser,
  adminUnapproveUser,
  adminToggleAdmin,
  adminDeleteUser,
} from "../api"

const SEARCHES_PER_PAGE = 5
const ALERTS_PER_PAGE = 5

const emptyForm = {
  pokemon_name: "",
  set_name: "",
  card_number: "",
  grading_type: "both",
  check_interval_mins: 5,
  listing_type: "buy_it_now",
  manual_market_price: "",
  min_price: "",
  max_price: "",
  is_active: true,
}


function formFromSearch(search) {
  return {
    pokemon_name: search.pokemon_name || "",
    set_name: search.set_name || "",
    card_number: search.card_number || "",
    grading_type: search.grading_type || "both",
    check_interval_mins: search.check_interval_mins || 5,
    listing_type: search.listing_type ?? "buy_it_now",
    manual_market_price:
      search.manual_market_price === null ? "" : String(search.manual_market_price),
    min_price: search.min_price === null ? "" : String(search.min_price),
    max_price: search.max_price === null ? "" : String(search.max_price),
    is_active: Boolean(search.is_active),
  }
}

function normalizePayload(form) {
  const pokemonName = form.pokemon_name.trim()
  const setName = form.set_name.trim()
  const cardNumber = form.card_number.trim()
  return {
    query_string: [pokemonName, setName, cardNumber].filter(Boolean).join(" ").toLowerCase(),
    pokemon_name: pokemonName || null,
    set_name: setName || null,
    card_number: cardNumber || null,
    grading_type: form.grading_type,
    check_interval_mins: Number(form.check_interval_mins) || 5,
    listing_type: form.listing_type,
    manual_market_price:
      form.manual_market_price === "" ? null : Number(form.manual_market_price),
    min_price: form.min_price === "" ? null : Number(form.min_price),
    max_price: form.max_price === "" ? null : Number(form.max_price),
    is_active: form.is_active,
  }
}

function formatMoney(value) {
  if (value === null || value === undefined) {
    return "—"
  }
  return `$${Number(value).toFixed(2)}`
}


function formatListingType(value) {
  if (value === "auction") {
    return "Auction"
  }
  if (value === "both") {
    return "Both"
  }
  return "Buy It Now"
}

function ResultBadge({ success }) {
  return (
    <span className={success ? "result-badge success" : "result-badge failure"}>
      {success ? "Success" : "Failed"}
    </span>
  )
}

function DiscordTestResult({ result }) {
  if (!result) {
    return null
  }
  return (
    <div className="test-result-card">
      <div className="test-result-header">
        <ResultBadge success={Boolean(result.success)} />
      </div>
      <p className="support-copy">{result.message}</p>
      <dl className="search-meta">
        <div>
          <dt>Message sent</dt>
          <dd>{result.success ? "Yes" : "No"}</dd>
        </div>
      </dl>
    </div>
  )
}

function EbayTestResult({ result }) {
  if (!result) {
    return null
  }
  const listings = Array.isArray(result.data) ? result.data : []
  const firstListing = listings[0] || null
  return (
    <div className="test-result-card">
      <div className="test-result-header">
        <ResultBadge success={Boolean(result.success)} />
      </div>
      <p className="support-copy">{result.message}</p>
      <dl className="search-meta">
        <div>
          <dt>Listings returned</dt>
          <dd>{listings.length}</dd>
        </div>
        {firstListing ? (
          <>
            <div>
              <dt>First result price</dt>
              <dd>{formatMoney(firstListing.price)}</dd>
            </div>
            <div>
              <dt>First result type</dt>
              <dd>{formatListingType(firstListing.listing_type)}</dd>
            </div>
            <div>
              <dt>First result title</dt>
              <dd>{firstListing.title || "—"}</dd>
            </div>
          </>
        ) : null}
      </dl>
    </div>
  )
}

function PokedataTestResult({ result }) {
  if (!result) {
    return null
  }
  const data = result.data || {}
  return (
    <div className="test-result-card">
      <div className="test-result-header">
        <ResultBadge success={Boolean(result.success)} />
      </div>
      <p className="support-copy">{result.message}</p>
      <dl className="search-meta">
        <div>
          <dt>Market price</dt>
          <dd>{formatMoney(data.market_price)}</dd>
        </div>
        <div>
          <dt>Product URL</dt>
          <dd>{data.product_url || "—"}</dd>
        </div>
      </dl>
    </div>
  )
}

function SearchForm({
  form,
  onChange,
  onSubmit,
  onCancel,
  submitLabel,
  busy,
}) {
  return (
    <form className="search-form" onSubmit={onSubmit}>

      <div className="search-grid">
        <label className="field">
          <span>Pokemon name</span>
          <input
            name="pokemon_name"
            value={form.pokemon_name}
            onChange={onChange}
            placeholder="Charizard"
            required
          />
        </label>

        <label className="field">
          <span>Set</span>
          <input
            name="set_name"
            value={form.set_name}
            onChange={onChange}
            placeholder="151"
            required
          />
        </label>

        <label className="field">
          <span>Card number</span>
          <input
            name="card_number"
            value={form.card_number}
            onChange={onChange}
            placeholder="199/165"
            required
          />
        </label>

        <label className="field">
          <span>Listing type</span>
          <select
            name="listing_type"
            value={form.listing_type}
            onChange={onChange}
          >
            <option value="buy_it_now">Buy It Now</option>
            <option value="auction">Auction</option>
            <option value="both">Both</option>
          </select>
        </label>

        <label className="field">
          <span>Manual market price</span>
          <input
            name="manual_market_price"
            type="number"
            step="0.01"
            min="0"
            value={form.manual_market_price}
            onChange={onChange}
            placeholder="200"
          />
        </label>


        <label className="field">
          <span>Min price</span>
          <input
            name="min_price"
            type="number"
            step="0.01"
            min="0"
            value={form.min_price}
            onChange={onChange}
            placeholder="100"
          />
        </label>

        <label className="field">
          <span>Max price</span>
          <input
            name="max_price"
            type="number"
            step="0.01"
            min="0"
            value={form.max_price}
            onChange={onChange}
            placeholder="220"
          />
        </label>

        <label className="field">
          <span>Grading</span>
          <select name="grading_type" value={form.grading_type} onChange={onChange}>
            <option value="both">Both</option>
            <option value="ungraded">Ungraded only</option>
            <option value="graded">Graded only</option>
          </select>
        </label>

        <label className="field">
          <span>Check interval (mins)</span>
          <input
            name="check_interval_mins"
            type="number"
            min="1"
            max="1440"
            value={form.check_interval_mins}
            onChange={onChange}
          />
        </label>

        <div className="field">
          <span>Search Status</span>
          <label className="toggle-field" style={{ height: '46px' }}>
            <input
              name="is_active"
              type="checkbox"
              checked={form.is_active}
              onChange={onChange}
            />
            <span>Active (polling eBay)</span>
          </label>
        </div>
      </div>

      <div className="form-actions">
        {onCancel ? (
          <button
            type="button"
            className="secondary-button"
            onClick={onCancel}
            disabled={busy}
          >
            Cancel
          </button>
        ) : null}
        <button type="submit" disabled={busy}>
          {busy ? "Saving..." : submitLabel}
        </button>
      </div>
    </form>
  )
}

export default function DashboardPage({ user, onUserChange, onLogout }) {
  const [searches, setSearches] = useState([])
  const [alerts, setAlerts] = useState([])
  const [createForm, setCreateForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm] = useState(emptyForm)
  const [view, setView] = useState("dashboard")
  const [adminUsers, setAdminUsers] = useState([])
  const [currentPage, setCurrentPage] = useState(1)
  const [alertsPage, setAlertsPage] = useState(1)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [discordChannelId, setDiscordChannelId] = useState(user.discord_channel_id || "")
  const [ebayAppId, setEbayAppId] = useState(user.ebay_app_id || "")
  const [ebayClientSecret, setEbayClientSecret] = useState("")
  const [pokedataQuery, setPokedataQuery] = useState("charizard 151 199/165")
  const [selectedTestSearchId, setSelectedTestSearchId] = useState("")
  const [testResults, setTestResults] = useState({
    discord: null,
    ebay: null,
    pokedata: null,
  })
  const [loading, setLoading] = useState(true)
  const [alertsLoading, setAlertsLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [settingsSaving, setSettingsSaving] = useState(false)
  const [testingAction, setTestingAction] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [settingsMessage, setSettingsMessage] = useState("")
  const [settingsError, setSettingsError] = useState("")

  const editingSearch = useMemo(
    () => searches.find((search) => search.id === editingId) || null,
    [editingId, searches],
  )
  const totalPages = Math.ceil(searches.length / SEARCHES_PER_PAGE)
  const paginatedSearches = useMemo(() => {
    const startIndex = (currentPage - 1) * SEARCHES_PER_PAGE
    return searches.slice(startIndex, startIndex + SEARCHES_PER_PAGE)
  }, [currentPage, searches])

  const paginatedAlerts = useMemo(() => {
    const startIndex = (alertsPage - 1) * ALERTS_PER_PAGE
    return alerts.slice(startIndex, startIndex + ALERTS_PER_PAGE)
  }, [alertsPage, alerts])
  const totalAlertsPages = Math.ceil(alerts.length / ALERTS_PER_PAGE)

  useEffect(() => {
    loadSearches()
    loadAlerts()
  }, [])

  useEffect(() => {
    setDiscordChannelId(user.discord_channel_id || "")
  }, [user.discord_channel_id])

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages)
    }
  }, [currentPage, totalPages])

  async function loadSearches() {
    setLoading(true)
    setError("")
    try {
      const data = await listSearches()
      setSearches(data)
      setCurrentPage(1)
      setSelectedTestSearchId((current) => {
        if (current && data.some((search) => search.id === current)) {
          return current
        }
        return data[0]?.id || ""
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load searches")
    } finally {
      setLoading(false)
    }
  }

  async function loadAlerts() {
    setAlertsLoading(true)
    try {
      const data = await listAlerts()
      setAlerts(data)
    } catch {
      setAlerts([])
    } finally {
      setAlertsLoading(false)
    }
  }

  async function loadAdminUsers() {
    if (!user.is_admin) return
    try {
      const data = await adminListUsers()
      setAdminUsers(data)
    } catch (err) {
      console.error("Failed to load admin users", err)
    }
  }

  async function handleApprove(userId, approved) {
    try {
      if (approved) {
        await adminApproveUser(userId)
      } else {
        await adminUnapproveUser(userId)
      }
      await loadAdminUsers()
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to update user")
    }
  }

  async function handleToggleAdmin(userId) {
    if (!window.confirm("Are you sure you want to change this user's admin status?")) return
    try {
      await adminToggleAdmin(userId)
      await loadAdminUsers()
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to toggle admin status")
    }
  }

  async function handleAdminDelete(userId) {
    if (!window.confirm("Are you sure you want to PERMANENTLY DELETE this user and all their searches? This cannot be undone.")) return
    try {
      await adminDeleteUser(userId)
      await loadAdminUsers()
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete user")
    }
  }

  function handleFormChange(setter) {
    return (event) => {
      const { name, type, checked, value } = event.target
      setter((current) => ({
        ...current,
        [name]: type === "checkbox" ? checked : value,
      }))
    }
  }

  async function handleCreate(event) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setMessage("")
    try {
      const created = await createSearch(normalizePayload(createForm))
      setSearches((current) => [created, ...current])
      setCurrentPage(1)
      setSelectedTestSearchId((current) => current || created.id)
      setCreateForm(emptyForm)
      setMessage("Search created.")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create search")
    } finally {
      setSaving(false)
    }
  }

  function startEditing(search) {
    setEditingId(search.id)
    setEditForm(formFromSearch(search))
    setError("")
    setMessage("")
  }

  function cancelEditing() {
    setEditingId(null)
    setEditForm(emptyForm)
  }

  async function handleUpdate(event) {
    event.preventDefault()
    if (!editingId) {
      return
    }
    setSaving(true)
    setError("")
    setMessage("")
    try {
      const updated = await updateSearch(editingId, normalizePayload(editForm))
      setSearches((current) =>
        current.map((search) => (search.id === editingId ? updated : search)),
      )
      setEditingId(null)
      setEditForm(emptyForm)
      setMessage("Search updated.")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update search")
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(searchId) {
    const confirmed = window.confirm("Delete this search?")
    if (!confirmed) {
      return
    }
    setSaving(true)
    setError("")
    setMessage("")
    try {
      await deleteSearch(searchId)
      setSearches((current) => current.filter((search) => search.id !== searchId))
      if (editingId === searchId) {
        cancelEditing()
      }
      setMessage("Search deleted.")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete search")
    } finally {
      setSaving(false)
    }
  }

  async function handleSaveSettings(event) {
    event.preventDefault()
    setSettingsSaving(true)
    setSettingsMessage("")
    setSettingsError("")
    try {
      const payload = {
        discord_channel_id: discordChannelId.trim() || null,
        ebay_app_id: ebayAppId.trim() || null,
      }
      if (ebayClientSecret.trim()) {
        payload.ebay_client_secret = ebayClientSecret.trim()
      }
      const updatedUser = await updateMe(payload)
      onUserChange(updatedUser)
      setEbayClientSecret("") // Clear input after save
      setSettingsMessage("Settings saved.")
    } catch (err) {
      setSettingsError(err instanceof Error ? err.message : "Could not save settings")
    } finally {
      setSettingsSaving(false)
    }
  }

  async function runDiscordTest() {
    setTestingAction("discord")
    try {
      const result = await testDiscord()
      setTestResults((current) => ({ ...current, discord: result }))
    } catch (err) {
      setTestResults((current) => ({
        ...current,
        discord: {
          success: false,
          message: err instanceof Error ? err.message : "Discord test failed.",
          data: null,
        },
      }))
    } finally {
      setTestingAction("")
    }
  }

  async function runEbayTest() {
    if (!selectedTestSearchId) {
      setTestResults((current) => ({
        ...current,
        ebay: { success: false, message: "Pick a search first.", data: [] },
      }))
      return
    }
    setTestingAction("ebay")
    try {
      const result = await testEbay({ search_query_id: selectedTestSearchId })
      setTestResults((current) => ({ ...current, ebay: result }))
    } catch (err) {
      setTestResults((current) => ({
        ...current,
        ebay: {
          success: false,
          message: err instanceof Error ? err.message : "eBay test failed.",
          data: [],
        },
      }))
    } finally {
      setTestingAction("")
    }
  }

  async function runPokedataTest() {
    setTestingAction("pokedata")
    try {
      const result = await testPokedata({
        query: pokedataQuery,
        debug_browser: false,
      })
      setTestResults((current) => ({ ...current, pokedata: result }))
    } catch (err) {
      setTestResults((current) => ({
        ...current,
        pokedata: {
          success: false,
          message: err instanceof Error ? err.message : "PokeDATA test failed.",
          data: null,
        },
      }))
    } finally {
      setTestingAction("")
    }
  }

  async function handleRefreshMarket(searchId) {
    setSaving(true)
    try {
      await refreshMarketPrice(searchId)
      await loadSearches()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh market price")
    } finally {
      setSaving(false)
    }
  }


  return (
    <main className="dashboard-layout">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">Signed in</p>
          <h1>{user.username}</h1>
        </div>
        <button type="button" className="secondary-button" onClick={onLogout}>
          Log out
        </button>
      </header>

      {user.is_admin && (
        <nav className="dashboard-nav">
          <button
            type="button"
            className={view === "dashboard" ? "is-active" : ""}
            onClick={() => setView("dashboard")}
          >
            Dashboard
          </button>
          <button
            type="button"
            className={view === "admin" ? "is-active" : ""}
            onClick={() => {
              setView("admin")
              loadAdminUsers()
            }}
          >
            Admin Panel
          </button>
        </nav>
      )}

      {view === "admin" && user.is_admin ? (
        <section className="dashboard-panel">
          <div className="panel-header">
            <h2>User Management</h2>
            <p className="support-copy">Approve or revoke access for users.</p>
          </div>
          <div className="admin-user-list">
            {adminUsers.map((u) => (
              <div key={u.id} className="admin-user-row">
                <div className="user-info">
                  <span className="username">{u.username}</span>
                  {u.is_admin && <span className="admin-badge">Admin</span>}
                  {!u.is_approved && <span className="pending-badge">Pending</span>}
                </div>
                <div className="user-actions">
                  {!u.is_admin && (
                    <button
                      type="button"
                      className={u.is_approved ? "danger-button" : "primary-button"}
                      onClick={() => handleApprove(u.id, !u.is_approved)}
                    >
                      {u.is_approved ? "Revoke Access" : "Approve"}
                    </button>
                  )}
                  {u.id !== user.id && (
                    <>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => handleToggleAdmin(u.id)}
                      >
                        {u.is_admin ? "Demote" : "Make Admin"}
                      </button>
                      <button
                        type="button"
                        className="danger-button"
                        onClick={() => handleAdminDelete(u.id)}
                      >
                        Delete
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : (
        <>
          <section className="dashboard-panel">
            <div className="panel-header">
              <h2>Searches</h2>
              <div className="panel-actions">
                <button
                  type="button"
                  className={showCreateForm ? "secondary-button" : "primary-button"}
                  onClick={() => setShowCreateForm(!showCreateForm)}
                >
                  {showCreateForm ? "Cancel" : "Create new search"}
                </button>
                <button type="button" className="secondary-button" onClick={loadSearches}>
                  Refresh
                </button>
              </div>
            </div>
            {showCreateForm && (
              <div className="create-form-overlay">
                <SearchForm
                  form={createForm}
                  onChange={handleFormChange(setCreateForm)}
                  onSubmit={(e) => {
                    handleCreate(e);
                    setShowCreateForm(false);
                  }}
                  submitLabel="Create search"
                  busy={saving}
                  onCancel={() => setShowCreateForm(false)}
                />
              </div>
            )}
            <p className="support-copy">
              Manage the eBay searches that feed your alerts.
            </p>
            {message ? <p className="form-success">{message}</p> : null}
            {error ? <p className="form-error">{error}</p> : null}
            {loading ? (
              <p className="support-copy">Loading searches...</p>
            ) : searches.length === 0 ? (
              <p className="support-copy">No searches yet.</p>
            ) : (
              <>
                <div className="search-list compact">
                  {paginatedSearches.map((search) => (
                    <article key={search.id} className="search-row-card">
                      <div className="search-row">
                        <div className="search-row-main">
                          <h3>{search.pokemon_name ? `${search.pokemon_name}${search.set_name ? ' - ' + search.set_name : ''}${search.card_number ? ' - ' + search.card_number : ''}` : search.query_string}</h3>
                          {search.market_price !== null && search.market_price !== undefined && (
                            <p className="support-copy" style={{ marginTop: '2px', fontSize: '0.9rem' }}>
                              Market price: <strong>{formatMoney(search.market_price)}</strong>
                            </p>
                          )}
                        </div>
                        <div className="card-actions">
                          <button
                            type="button"
                            className="secondary-button"
                            onClick={() => handleRefreshMarket(search.id)}
                            disabled={saving}
                          >
                            Refresh Price
                          </button>
                          <button
                            type="button"
                            className="secondary-button"
                            onClick={() => startEditing(search)}
                            disabled={saving}
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            className="danger-button"
                            onClick={() => handleDelete(search.id)}
                            disabled={saving}
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                      {editingId === search.id ? (
                        <div className="inline-edit-panel">
                          <SearchForm
                            form={editForm}
                            onChange={handleFormChange(setEditForm)}
                            onSubmit={handleUpdate}
                            onCancel={cancelEditing}
                            submitLabel="Save changes"
                            busy={saving}

                          />
                        </div>
                      ) : null}
                    </article>
                  ))}
                </div>
                <div className="pagination-row">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                    disabled={currentPage === 1}
                  >
                    Previous
                  </button>
                  <p className="support-copy pagination-label">
                    Page {currentPage} of {totalPages}
                  </p>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
                    disabled={currentPage === totalPages}
                  >
                    Next
                  </button>
                </div>
              </>
            )}
          </section>


          <section className="dashboard-grid single-column">
            <section className="dashboard-panel">
              <div className="panel-header">
                <h2>Settings & Tests</h2>
              </div>
              
              <div className="settings-test-layout">
                <div className="settings-group">
                  <p className="support-copy">Configure your Discord alert destination.</p>
                  <form className="search-form" onSubmit={handleSaveSettings}>
                    <label className="field">
                      <span>Discord channel ID</span>
                      <input
                        value={discordChannelId}
                        onChange={(event) => setDiscordChannelId(event.target.value)}
                        placeholder="123456789012345678"
                      />
                    </label>

                    <div style={{ display: "grid", gap: "16px" }}>
                      <p className="support-copy" style={{ margin: 0 }}>
                        Personal eBay API (Optional)
                      </p>
                      <label className="field">
                        <span>eBay App ID</span>
                        <input
                          value={ebayAppId}
                          onChange={(event) => setEbayAppId(event.target.value)}
                          placeholder="Your-App-ID"
                        />
                      </label>
                      <label className="field">
                        <span>eBay Client Secret {user.has_ebay_secret && "(Already set)"}</span>
                        <input
                          type="password"
                          value={ebayClientSecret}
                          onChange={(event) => setEbayClientSecret(event.target.value)}
                          placeholder={user.has_ebay_secret ? "••••••••••••••••" : "Your-Client-Secret"}
                        />
                      </label>
                    </div>
                    {settingsMessage ? <p className="form-success">{settingsMessage}</p> : null}
                    {settingsError ? <p className="form-error">{settingsError}</p> : null}
                    <div className="form-actions">
                      <button type="submit" disabled={settingsSaving}>
                        {settingsSaving ? "Saving..." : "Save settings"}
                      </button>
                    </div>
                  </form>
                </div>

                <div className="test-divider" />

                <div className="test-stack">
                  <p className="support-copy">Verify your integrations manually.</p>
                  <div className="test-row">
                    <button
                      type="button"
                      onClick={runDiscordTest}
                      disabled={testingAction === "discord"}
                    >
                      {testingAction === "discord" ? "Testing..." : "Test Discord"}
                    </button>
                    <p className="support-copy">
                      {testResults.discord?.message || "Send a Discord test message."}
                    </p>
                    <DiscordTestResult result={testResults.discord} />
                  </div>

                  <div className="test-row">
                    <label className="field">
                      <span>Search for eBay test</span>
                      <select
                        value={selectedTestSearchId}
                        onChange={(event) => setSelectedTestSearchId(event.target.value)}
                      >
                        <option value="">Select a search</option>
                        {searches.map((search) => (
                          <option key={search.id} value={search.id}>
                            {search.query_string}
                          </option>
                        ))}
                      </select>
                    </label>
                    <button
                      type="button"
                      onClick={runEbayTest}
                      disabled={testingAction === "ebay"}
                    >
                      {testingAction === "ebay" ? "Testing..." : "Test eBay (Top 5)"}
                    </button>
                    <p className="support-copy">
                      {testResults.ebay?.message || "Fetch top 5 listings for one saved search."}
                    </p>
                    <EbayTestResult result={testResults.ebay} />
                  </div>

                  <div className="test-row">
                    <label className="field">
                      <span>PokeDATA query</span>
                      <input
                        value={pokedataQuery}
                        onChange={(event) => setPokedataQuery(event.target.value)}
                      />
                    </label>
                    <button
                      type="button"
                      onClick={runPokedataTest}
                      disabled={testingAction === "pokedata"}
                    >
                      {testingAction === "pokedata" ? "Testing..." : "Test PokeDATA"}
                    </button>
                    <p className="support-copy">
                      {testResults.pokedata?.message || "Check current market-price scraping."}
                    </p>
                    <PokedataTestResult result={testResults.pokedata} />
                  </div>
                </div>
              </div>
            </section>
          </section>

          <section className="dashboard-panel">
            <div className="panel-header">
              <h2>Recent alerts</h2>
              <button type="button" className="secondary-button" onClick={loadAlerts}>
                Refresh
              </button>
            </div>
            {alertsLoading ? (
              <p className="support-copy">Loading alerts...</p>
            ) : alerts.length === 0 ? (
              <p className="support-copy">No alerts sent yet.</p>
            ) : (
              <div className="alerts-list">
                {paginatedAlerts.map((alert) => (
                  <article key={alert.id} className="alert-card with-image">
                    {alert.image_url && (
                      <div className="alert-image-container">
                        <img src={alert.image_url} alt={alert.title} />
                      </div>
                    )}
                    <div className="alert-content">
                      <div className="search-card-header">
                        <div>
                          <h3>{alert.title}</h3>
                          <p className="support-copy">{new Date(alert.sent_at).toLocaleString()}</p>
                        </div>
                        <a
                          className="link-button"
                          href={alert.listing_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          View listing
                        </a>
                      </div>
                      <dl className="search-meta">
                        <div>
                          <dt>Listing price</dt>
                          <dd>{formatMoney(alert.listing_price)}</dd>
                        </div>
                        <div>
                          <dt>Market price</dt>
                          <dd>{formatMoney(alert.market_price)}</dd>
                        </div>
                        {alert.pct_below_market != null && (
                        <div>
                          <dt>{alert.pct_below_market > 0 ? 'Below market' : 'Above market'}</dt>
                          <dd style={{ color: alert.pct_below_market > 0 ? '#99f0b4' : '#ff8d8d' }}>
                            {Math.abs(alert.pct_below_market * 100).toFixed(1)}%
                          </dd>
                        </div>
                        )}
                        <div>
                          <dt>Item ID</dt>
                          <dd>{alert.ebay_item_id}</dd>
                        </div>
                      </dl>
                    </div>
                  </article>
                ))}
              </div>
            )}
            {totalAlertsPages > 1 && (
              <div className="pagination-row">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setAlertsPage((page) => Math.max(1, page - 1))}
                  disabled={alertsPage === 1}
                >
                  Previous
                </button>
                <p className="support-copy pagination-label">
                  Page {alertsPage} of {totalAlertsPages}
                </p>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setAlertsPage((page) => Math.min(totalAlertsPages, page + 1))}
                  disabled={alertsPage === totalAlertsPages}
                >
                  Next
                </button>
              </div>
            )}
          </section>
        </>
      )}
    </main>
  )
}
