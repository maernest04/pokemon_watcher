import { DiscordTestResult, EbayTestResult, PokedataTestResult } from "./TestResults"

export function SettingsPanel({
  user,
  handleSaveSettings,
  discordChannelId,
  setDiscordChannelId,
  ebayAppId,
  setEbayAppId,
  showEbaySecret,
  setShowEbaySecret,
  ebayClientSecret,
  setEbayClientSecret,
  settingsMessage,
  settingsError,
  settingsSaving,
  runDiscordTest,
  testingAction,
  testResults,
  selectedTestSearchId,
  setSelectedTestSearchId,
  searches,
  runEbayTest,
  pokedataQuery,
  setPokedataQuery,
  runPokedataTest
}) {
  return (
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
                  <div className="password-input-container">
                    <input
                      type={showEbaySecret ? "text" : "password"}
                      value={ebayClientSecret}
                      onChange={(event) => setEbayClientSecret(event.target.value)}
                      placeholder={user.has_ebay_secret ? "••••••••••••••••" : "Your-Client-Secret"}
                    />
                    <button
                      type="button"
                      className="password-toggle-button"
                      onClick={() => setShowEbaySecret(!showEbaySecret)}
                      title={showEbaySecret ? "Hide secret" : "Show secret"}
                    >
                      {showEbaySecret ? "🙈" : "👁️"}
                    </button>
                  </div>
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
  )
}
