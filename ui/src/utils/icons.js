import * as LucideIcons from 'lucide-vue-next'
import { typeToIconMap } from '@/constants/devices'

/**
 * Resolves a Lucide icon component based on a name or device type.
 * @param {string} name - The icon name, device type, or legacy key.
 * @returns {Component} The Lucide icon component or HelpCircle as fallback.
 */
export function getIcon(name) {
    if (!name) return LucideIcons.HelpCircle

    // 1. Try direct match in Lucide (PascalCase or exactly matching key)
    if (LucideIcons[name]) return LucideIcons[name]

    // 2. Try mapping from constants/devices.js (Device Type -> Icon Name)
    // We check case-insensitively for the type
    const normalizedName = name.trim()
    for (const [type, iconName] of Object.entries(typeToIconMap)) {
        if (type.toLowerCase() === normalizedName.toLowerCase()) {
            if (LucideIcons[iconName]) return LucideIcons[iconName]
        }
    }

    // 3. Legacy / Manual mapping (kebab-case -> PascalCase or specific map)
    const legacyMap = {
        'smartphone': 'Smartphone',
        'tablet': 'Tablet',
        'laptop': 'Laptop',
        'monitor': 'Monitor',
        'server': 'Server',
        'router': 'Router',
        'network': 'Network',
        'layers': 'Layers',
        'rss': 'Rss',
        'tv': 'Tv',
        'speaker': 'Speaker',
        'play': 'Play',
        'cpu': 'Cpu',
        'lightbulb': 'Lightbulb',
        'plug': 'Plug',
        'microchip': 'Microchip',
        'camera': 'Camera',
        'waves': 'Waves',
        'printer': 'Printer',
        'hard-drive': 'HardDrive',
        'gamepad-2': 'Gamepad2',
        'help-circle': 'HelpCircle',
        'computer-desktop': 'Monitor',
        'device-laptop': 'Laptop',
        'device-phone-mobile': 'Smartphone',
        'device-tablet': 'Tablet',
        'server-stack': 'Database',
        'bolt': 'Zap',
        'activity': 'Activity',
        'wifi': 'Wifi',
        'database': 'Database',
        'zap-off': 'ZapOff',
        'ticket': 'Ticket'
    }

    const mappedName = legacyMap[normalizedName] || legacyMap[normalizedName.toLowerCase()]
    if (mappedName && LucideIcons[mappedName]) return LucideIcons[mappedName]

    // 4. Auto convert kebab-case to PascalCase
    const pascal = normalizedName.split('-')
        .map(p => p.charAt(0).toUpperCase() + p.slice(1).toLowerCase())
        .join('')
    if (LucideIcons[pascal]) return LucideIcons[pascal]

    // Fallback
    return LucideIcons.HelpCircle
}
