import { useEffect, useMemo, useState } from "react"
import { SearchList } from "../components/SearchList"
import { SettingsPanel } from "../components/SettingsPanel"
import { AlertsList } from "../components/AlertsList"
import { AdminPanel } from "../components/AdminPanel"
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
  adminToggleSearch,
  adminDeleteSearch,
  adminChangePassword,
} from "../api"


const SEARCHES_PER_PAGE = 5
const ALERTS_PER_PAGE = 5

const emptyForm = {
  pokemon_name: "",
  set_name: "",
  card_number: "",
  grading_type: "both",
  language: "english",
  check_interval_mins: 5,
  listing_type: "buy_it_now",
  pokedata_url: "",
  manual_market_price: "",
  min_price: "",
  max_price: "",
  hide_above_market: false,
  is_active: true,
}


function formFromSearch(search) {
  return {
    pokemon_name: search.pokemon_name || "",
    set_name: search.set_name || "",
    card_number: search.card_number || "",
    grading_type: search.grading_type || "both",
    language: search.language || "english",
    check_interval_mins: search.check_interval_mins || 5,
    listing_type: search.listing_type ?? "buy_it_now",
    pokedata_url: search.pokedata_url || "",
    manual_market_price: search.manual_market_price === null ? "" : String(search.manual_market_price),
    min_price: search.min_price === null ? "" : String(search.min_price),
    max_price: search.max_price === null ? "" : String(search.max_price),
    hide_above_market: Boolean(search.hide_above_market),
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
    language: form.language || "english",
    check_interval_mins: Number(form.check_interval_mins) || 5,
    listing_type: form.listing_type,
    pokedata_url: form.pokedata_url.trim() || null,
    manual_market_price: form.manual_market_price === "" ? null : Number(form.manual_market_price),
    min_price: form.min_price === "" ? null : Number(form.min_price),
    max_price: form.max_price === "" ? null : Number(form.max_price),
    hide_above_market: form.hide_above_market,
    is_active: form.is_active,
  }
}


export default function DashboardPage({ user, onUserChange, onLogout }) {
  const [searches, setSearches] = useState([])
  const [alerts, setAlerts] = useState([])
  const [createForm, setCreateForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm] = useState(emptyForm)
  const [pollingIds, setPollingIds] = useState(new Set())
  const [view, setView] = useState("dashboard")
  const [adminUsers, setAdminUsers] = useState([])
  const [expandedAdminUserIds, setExpandedAdminUserIds] = useState(new Set())
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
  const [showEbaySecret, setShowEbaySecret] = useState(false)
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

  async function handleAdminToggleSearch(userId, searchId) {
    try {
      await adminToggleSearch(userId, searchId)
      await loadAdminUsers()
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to toggle search")
    }
  }

  async function handleAdminDeleteSearch(userId, searchId) {
    if (!window.confirm("Are you sure you want to PERMANENTLY DELETE this search? This cannot be undone.")) return
    try {
      await adminDeleteSearch(userId, searchId)
      await loadAdminUsers()
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete search")
    }
  }

  async function handleAdminResetPassword(userId) {
    const newPassword = window.prompt("Enter new password for this user (min 8 chars):")
    if (!newPassword) return
    if (newPassword.length < 8) {
      alert("Password must be at least 8 characters.")
      return
    }
    try {
      await adminChangePassword(userId, { new_password: newPassword })
      alert("Password reset successfully.")
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to reset password")
    }
  }


  function toggleAdminUserExpand(userId) {
    setExpandedAdminUserIds((prev) => {
      const next = new Set(prev)
      if (next.has(userId)) next.delete(userId)
      else next.add(userId)
      return next
    })
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

  async function pollForMarketPrice(searchId) {
    setPollingIds((prev) => new Set([...prev, searchId]))
    try {
      for (let i = 0; i < 15; i++) {
        await new Promise((r) => setTimeout(r, 2000))
        try {
          const list = await listSearches()
          const updated = list.find((s) => s.id === searchId)
          if (updated) {
            const hasPrice = updated.market_price !== null && updated.market_price !== undefined;
            const urlRemoved = !updated.pokedata_url;
            if (hasPrice) {
              setSearches(list)
              return
            }
          }
        } catch {
          // ignore error and continue polling
        }
      }
    } finally {
      setPollingIds((prev) => {
        const next = new Set(prev)
        next.delete(searchId)
        return next
      })
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
      const needsPrice =
        created.language === "english" &&
        ((created.market_price === null || created.market_price === undefined) || created.pokedata_url)
      setMessage(
        needsPrice
          ? "Search created. Fetching market price..."
          : created.language === "japanese"
            ? "Search created. PokeData market price is for English only."
            : "Search created."
      )
      if (needsPrice) {
        pollForMarketPrice(created.id)
      }
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
      const payload = normalizePayload(editForm)
      const updated = await updateSearch(editingId, payload)
      setSearches((current) =>
        current.map((search) => (search.id === editingId ? updated : search)),
      )
      setEditingId(null)
      setEditForm(emptyForm)
      const needsPrice = payload.pokedata_url && updated.language === "english"
      setMessage(needsPrice ? "Search updated. Fetching new market price..." : "Search updated.")
      if (needsPrice) {
        pollForMarketPrice(updated.id)
      }
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
    setError("")
    setPollingIds((prev) => new Set([...prev, searchId]))
    try {
      await refreshMarketPrice(searchId)
      await loadSearches()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh market price")
    } finally {
      setPollingIds((prev) => {
        const next = new Set(prev)
        next.delete(searchId)
        return next
      })
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
        <AdminPanel 
          user={user} 
          adminUsers={adminUsers} 
          expandedAdminUserIds={expandedAdminUserIds}
          toggleAdminUserExpand={toggleAdminUserExpand}
          handleApprove={handleApprove}
          handleToggleAdmin={handleToggleAdmin}
          handleAdminResetPassword={handleAdminResetPassword}
          handleAdminDelete={handleAdminDelete}
          handleAdminToggleSearch={handleAdminToggleSearch}
          handleAdminDeleteSearch={handleAdminDeleteSearch}
        />
      ) : (
        <>
          <SearchList 
            showCreateForm={showCreateForm}
            setShowCreateForm={setShowCreateForm}
            loadSearches={loadSearches}
            createForm={createForm}
            setCreateForm={setCreateForm}
            handleCreate={handleCreate}
            saving={saving}
            message={message}
            error={error}
            loading={loading}
            searches={searches}
            paginatedSearches={paginatedSearches}
            pollingIds={pollingIds}
            handleRefreshMarket={handleRefreshMarket}
            startEditing={startEditing}
            handleDelete={handleDelete}
            editingId={editingId}
            editForm={editForm}
            setEditForm={setEditForm}
            handleUpdate={handleUpdate}
            cancelEditing={cancelEditing}
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
            totalPages={totalPages}
            handleFormChange={handleFormChange}
          />


          <SettingsPanel 
            user={user}
            handleSaveSettings={handleSaveSettings}
            discordChannelId={discordChannelId}
            setDiscordChannelId={setDiscordChannelId}
            ebayAppId={ebayAppId}
            setEbayAppId={setEbayAppId}
            showEbaySecret={showEbaySecret}
            setShowEbaySecret={setShowEbaySecret}
            ebayClientSecret={ebayClientSecret}
            setEbayClientSecret={setEbayClientSecret}
            settingsMessage={settingsMessage}
            settingsError={settingsError}
            settingsSaving={settingsSaving}
            runDiscordTest={runDiscordTest}
            testingAction={testingAction}
            testResults={testResults}
            selectedTestSearchId={selectedTestSearchId}
            setSelectedTestSearchId={setSelectedTestSearchId}
            searches={searches}
            runEbayTest={runEbayTest}
            pokedataQuery={pokedataQuery}
            setPokedataQuery={setPokedataQuery}
            runPokedataTest={runPokedataTest}
          />

          <AlertsList 
            loadAlerts={loadAlerts}
            alertsLoading={alertsLoading}
            alerts={alerts}
            paginatedAlerts={paginatedAlerts}
            totalAlertsPages={totalAlertsPages}
            alertsPage={alertsPage}
            setAlertsPage={setAlertsPage}
          />
        </>
      )}
    </main>
  )
}
