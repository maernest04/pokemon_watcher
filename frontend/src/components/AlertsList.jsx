import { formatMoney } from "../utils/formatters"
import "./AlertsList.css"

export function AlertsList({
  loadAlerts,
  alertsLoading,
  alerts,
  paginatedAlerts,
  totalAlertsPages,
  alertsPage,
  setAlertsPage
}) {
  return (
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
                    <p className="support-copy">
                      {new Date(alert.sent_at.endsWith('Z') ? alert.sent_at : alert.sent_at + 'Z').toLocaleString()}
                    </p>
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
  )
}
