import { formatMoney, formatListingType } from "../utils/formatters";

export function ResultBadge({ success }) {
  return (
    <span className={success ? "result-badge success" : "result-badge failure"}>
      {success ? "Success" : "Failed"}
    </span>
  )
}

export function DiscordTestResult({ result }) {
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

export function EbayTestResult({ result }) {
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

export function PokedataTestResult({ result }) {
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
