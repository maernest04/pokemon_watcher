export function SearchForm({
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
          <span>PokeDATA URL override</span>
          <input
            name="pokedata_url"
            value={form.pokedata_url}
            onChange={onChange}
            placeholder="https://www.pokedata.io/card/..."
          />
        </label>

        <label className="field">
          <span>Manual price override</span>
          <input
            name="manual_market_price"
            type="number"
            step="0.01"
            min="0"
            value={form.manual_market_price}
            onChange={onChange}
            placeholder="95.50"
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
          <span>Language</span>
          <select name="language" value={form.language || "english"} onChange={onChange}>
            <option value="english">English</option>
            <option value="japanese">Japanese</option>
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
          <span>Market Price Filter</span>
          <label className="toggle-field" style={{ height: '46px' }}>
            <input
              name="hide_above_market"
              type="checkbox"
              checked={form.hide_above_market}
              onChange={onChange}
            />
            <span>Hide above market price</span>
          </label>
        </div>

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
