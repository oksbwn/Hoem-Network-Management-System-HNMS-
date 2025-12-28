import { DateTime } from 'luxon'

/**
 * Formats a date string to the user's local equivalent using Luxon.
 * Handles ISO strings and SQL-style space-separated strings as UTC.
 * @param {string} timestamp 
 * @returns {string} Formatted local date string
 */
export const formatDate = (timestamp) => {
    if (!timestamp) return 'Never'
    
    try {
        let dt
        // Handle SQL style "YYYY-MM-DD HH:MM:SS" -> assume LOCAL (Legacy data)
        // New data using strict UTC will be ISO format (with T), so it goes to the else block.
        if (typeof timestamp === 'string' && timestamp.includes(' ')) {
            dt = DateTime.fromSQL(timestamp, { zone: 'local' })
        } else {
            // ISO format handling
            // Problem: The backend is sending timestamps like "14:30+00:00" when the event was actually at "14:30 Local".
            // (System clock mismatch).
            // Fix: We discard the timezone offset from the string and force the browser/Luxon to treat the
            // numerical date parts as belonging to the LOCAL timezone.
            let pureIso = timestamp
            if (timestamp.includes('+')) pureIso = timestamp.split('+')[0]
            if (timestamp.endsWith('Z')) pureIso = timestamp.slice(0, -1)
            
            dt = DateTime.fromISO(pureIso, { zone: 'local' })
        }

        if (!dt.isValid) return timestamp
        
        // Convert to local system zone
        return dt.toLocal().toFormat('dd/MM/yyyy HH:mm')
    } catch (e) {
        return timestamp
    }
}

/**
 * Returns a relative time string (e.g. "5m ago")
 * @param {string} timestamp 
 * @returns {string} Relative time string
 */
export const formatRelativeTime = (timestamp) => {
    if (!timestamp) return 'Never'
    
    try {
        let dt
        if (typeof timestamp === 'string' && timestamp.includes(' ')) {
            dt = DateTime.fromSQL(timestamp, { zone: 'local' })
        } else {
            // ISO format handling - SAME FIX AS formatDate
            // Strip timezone offset and force local interpretation to handle system clock mismatches.
            let pureIso = timestamp
            if (timestamp.includes('+')) pureIso = timestamp.split('+')[0]
            if (timestamp.endsWith('Z')) pureIso = timestamp.slice(0, -1)
            
            dt = DateTime.fromISO(pureIso, { zone: 'local' })
        }

        if (!dt.isValid) return 'Never'
        
        return dt.toRelative()
    } catch {
        return 'Never'
    }
}
