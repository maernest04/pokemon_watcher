import { useEffect, useState } from "react"
import DashboardPage from "./pages/DashboardPage"
import AuthPage from "./pages/AuthPage"
import { getMe, login, register, setToken } from "./api"

export default function App() {
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(true)

  useEffect(() => {
    let mounted = true

    async function loadUser() {
      try {
        const me = await getMe()
        if (mounted) {
          setUser(me)
        }
      } catch {
        setToken("")
      } finally {
        if (mounted) {
          setBooting(false)
        }
      }
    }

    loadUser()

    return () => {
      mounted = false
    }
  }, [])

  async function handleAuthenticated(mode, credentials) {
    const action = mode === "signup" ? register : login
    const authData = await action(credentials)
    setToken(authData.access_token)
    const me = await getMe()
    setUser(me)
  }

  function handleLogout() {
    setToken("")
    setUser(null)
  }

  if (booting) {
    return (
      <main className="auth-layout">
        <section className="auth-panel">
          <h1>Pokemon Watcher</h1>
          <p className="support-copy">Loading...</p>
        </section>
      </main>
    )
  }

  if (!user) {
    return <AuthPage onAuthenticated={handleAuthenticated} />
  }

  return <DashboardPage user={user} onUserChange={setUser} onLogout={handleLogout} />
}
