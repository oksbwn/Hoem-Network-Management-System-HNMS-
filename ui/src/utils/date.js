import { DateTime } from 'luxon'

/**
 * Robust date formatter.
 * @param {string} timestamp 
 * @returns {string} local format
 */
export const formatDate = (timestamp) => {
  if (!timestamp) return 'Never'
  try {
    const dt = DateTime.fromISO(timestamp)
    if (!dt.isValid) {
        // Try fallback for DuckDB strings
        const dt2 = DateTime.fromSQL(timestamp)
        return dt2.isValid ? dt2.toFormat('dd/MM/yyyy HH:mm') : timestamp
    }
    return dt.toFormat('dd/MM/yyyy HH:mm')
  } catch (e) {
    return timestamp
  }
}

/**
 * Relative time (e.g. 5m ago)
 * @param {string} timestamp 
 * @returns {string} 
 */
export const formatRelativeTime = (timestamp) => {
    if (!timestamp) return 'Never'
    try {
        const dt = DateTime.fromISO(timestamp)
        if (!dt.isValid) {
            const dt2 = DateTime.fromSQL(timestamp)
            return dt2.isValid ? dt2.toRelative() : 'Never'
        }
        return dt.toRelative()
    } catch {
        return 'Never'
    }
}
