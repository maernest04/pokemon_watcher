import { useState } from "react"

const initialForm = {
  username: "",
  password: "",
}

export default function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState("login")
  const [form, setForm] = useState(initialForm)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError("")
    try {
      const result = await onAuthenticated(mode, form)
      if (result && result.message) {
        setMessage(result.message)
        setForm(initialForm)
      } else {
        setForm(initialForm)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    } finally {
      setBusy(false)
    }
  }

  function updateField(event) {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }))
  }

  return (
    <main className="auth-layout">
      <section className="auth-panel">
        <div className="auth-copy">
          <p className="eyebrow">Pokemon Watcher</p>
          <h1>{mode === "login" ? "Log in" : "Create account"}</h1>
          <p className="support-copy">
            Track new eBay listings, compare against market pricing, and keep
            your alerts flowing into Discord.
          </p>
        </div>

        <div className="auth-toggle" role="tablist" aria-label="Auth mode">
          <button
            type="button"
            className={mode === "login" ? "is-active" : ""}
            onClick={() => {
              setMode("login")
              setError("")
            }}
          >
            Login
          </button>
          <button
            type="button"
            className={mode === "signup" ? "is-active" : ""}
            onClick={() => {
              setMode("signup")
              setError("")
            }}
          >
            Sign up
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            <span>Username</span>
            <input
              name="username"
              value={form.username}
              onChange={updateField}
              autoComplete="username"
              required
            />
          </label>
          <label>
            <span>Password</span>
            <input
              name="password"
              type="password"
              value={form.password}
              onChange={updateField}
              autoComplete={
                mode === "login" ? "current-password" : "new-password"
              }
              required
            />
          </label>
          {error ? <p className="form-error">{error}</p> : null}
          {message ? <p className="form-success">{message}</p> : null}
          <button type="submit" disabled={busy}>
            {busy ? "Working..." : mode === "login" ? "Login" : "Create account"}
          </button>
        </form>
      </section>
    </main>
  )
}
