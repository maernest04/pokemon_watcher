export function formatMoney(value) {
  if (value === null || value === undefined) {
    return "—"
  }
  return `$${Number(value).toFixed(2)}`
}

export function formatListingType(value) {
  if (value === "auction") {
    return "Auction"
  }
  if (value === "both") {
    return "Both"
  }
  return "Buy It Now"
}

export function formatLanguage(value) {
  if (value === "japanese") {
    return "Japanese"
  }
  return "English"
}
