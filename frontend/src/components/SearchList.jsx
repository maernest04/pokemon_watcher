import { SearchForm } from "./SearchForm"
import { formatLanguage, formatMoney } from "../utils/formatters"
import "./SearchList.css"

export function SearchList({
  showCreateForm,
  setShowCreateForm,
  loadSearches,
  createForm,
  setCreateForm,
  handleCreate,
  saving,
  message,
  error,
  loading,
  searches,
  paginatedSearches,
  pollingIds,
  handleRefreshMarket,
  startEditing,
  handleDelete,
  editingId,
  editForm,
  setEditForm,
  handleUpdate,
  cancelEditing,
  currentPage,
  setCurrentPage,
  totalPages,
  handleFormChange
}) {
  return (
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
                    <p className="support-copy" style={{ marginTop: '2px', fontSize: '0.85rem', opacity: 0.85 }}>
                      Language: {formatLanguage(search.language)}
                    </p>
                    {pollingIds.has(search.id) ? (
                      <div className="support-copy" style={{ marginTop: '4px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-color)', fontWeight: 500 }}>
                        <div className="spinner-small" />
                        Fetching latest market price...
                      </div>
                    ) : (
                      search.market_price !== null && search.market_price !== undefined && (
                        <p className="support-copy" style={{ marginTop: '2px', fontSize: '0.9rem' }}>
                          Market price: <strong>{formatMoney(search.market_price)}</strong>
                        </p>
                      )
                    )}
                    {search.hide_above_market && (
                      <p className="support-copy" style={{ marginTop: '2px', fontSize: '0.85rem', color: 'var(--accent-color)' }}>
                        Filtering out listings above market price
                      </p>
                    )}
                  </div>
                  <div className="card-actions">
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => handleRefreshMarket(search.id)}
                      disabled={saving || search.language === "japanese"}
                      title={search.language === "japanese" ? "PokeData market prices apply to English listings only." : undefined}
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
  )
}
