const API_BASE = 'http://localhost:8000'

export async function fetchTopology() {
  try {
    // Add cache-busting parameter to avoid browser cache issues
    const timestamp = Date.now()
    const resp = await fetch(`${API_BASE}/topology?t=${timestamp}`, {
      method: 'GET',
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    })
    console.log('Topology response status:', resp.status)
    console.log('Topology response headers:', Object.fromEntries(resp.headers.entries()))
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const data = await resp.json()
    console.log('Topology data received:', data)
    return data
  } catch (error) {
    console.error('Failed to fetch topology:', error)
    return { nodes: [], edges: [] }
  }
}

export async function fetchDevice(deviceId: string) {
  try {
    const resp = await fetch(`${API_BASE}/devices/${deviceId}`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to fetch device:', error)
    return {}
  }
}

export async function fetchInterfaces(deviceId: string) {
  try {
    const resp = await fetch(`${API_BASE}/interfaces/${deviceId}`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to fetch interfaces:', error)
    return []
  }
}

export async function fetchInterfaceMetrics(deviceId: string, ifIndex: number) {
  try {
    const resp = await fetch(`${API_BASE}/metrics/${deviceId}/${ifIndex}`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to fetch interface metrics:', error)
    return { lastCounters: {} }
  }
}

export async function triggerDiscovery() {
  try {
    const timestamp = Date.now()
    const resp = await fetch(`${API_BASE}/topology/discover?t=${timestamp}`, { 
      method: 'POST',
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    })
    console.log('Discovery response status:', resp.status)
    console.log('Discovery response headers:', Object.fromEntries(resp.headers.entries()))
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const data = await resp.json()
    console.log('Discovery data received:', data)
    return data
  } catch (error) {
    console.error('Failed to trigger discovery:', error)
    return { nodes: [], edges: [] }
  }
}

export async function getNetworkStatus() {
  try {
    const timestamp = Date.now()
    const resp = await fetch(`${API_BASE}/topology/network-status?t=${timestamp}`, {
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to fetch network status:', error)
    return { connected: false, error: 'Unable to check network status' }
  }
}

export async function getUnknownVendors() {
  try {
    const timestamp = Date.now()
    const resp = await fetch(`${API_BASE}/oui/debug/unknown-vendors?t=${timestamp}`, {
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to fetch unknown vendors:', error)
    return { status: 'error', data: { unknown_devices: [], count: 0, total_devices: 0 } }
  }
}

export async function getUserMappings() {
  try {
    const timestamp = Date.now()
    const resp = await fetch(`${API_BASE}/user-settings/mappings?t=${timestamp}`, {
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to fetch user mappings:', error)
    return []
  }
}

export async function createUserMapping(mapping: {
  identifier: string
  device_type: string
  vendor: string
  model: string
  hostname?: string
  notes?: string
}) {
  try {
    const resp = await fetch(`${API_BASE}/user-settings/mappings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      },
      body: JSON.stringify(mapping)
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to create user mapping:', error)
    throw error
  }
}

export async function applyUserMappings() {
  try {
    const resp = await fetch(`${API_BASE}/user-settings/apply-to-devices`, {
      method: 'POST',
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to apply user mappings:', error)
    throw error
  }
}

// Device History API functions
export async function fetchDeviceHistory(deviceId: string, limit = 50, eventType?: string, daysBack = 30) {
  try {
    const params = new URLSearchParams({
      limit: limit.toString(),
      days_back: daysBack.toString()
    })
    if (eventType) params.append('event_type', eventType)
    
    const resp = await fetch(`${API_BASE}/device-history/devices/${deviceId}/history?${params}`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to fetch device history:', error)
    return []
  }
}

export async function fetchDeviceSessionStats(deviceId: string, daysBack = 30) {
  try {
    const resp = await fetch(`${API_BASE}/device-history/devices/${deviceId}/history/stats?days_back=${daysBack}`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to fetch device session stats:', error)
    return null
  }
}

export async function fetchRecentEvents(hoursBack = 24) {
  try {
    const resp = await fetch(`${API_BASE}/device-history/history/recent?hours_back=${hoursBack}`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to fetch recent events:', error)
    return []
  }
}

export async function fetchHistorySummary(daysBack = 7) {
  try {
    const resp = await fetch(`${API_BASE}/device-history/history/summary?days_back=${daysBack}`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to fetch history summary:', error)
    return null
  }
}

// Device Grouping API functions
export async function fetchGroupedDevices(groupBy: string = 'vendor') {
  try {
    const resp = await fetch(`${API_BASE}/devices/grouped?group_by=${groupBy}`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to fetch grouped devices:', error)
    return {}
  }
}

export async function fetchGroupingStats() {
  try {
    const resp = await fetch(`${API_BASE}/devices/grouped/stats`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to fetch grouping stats:', error)
    return {}
  }
}

// Notification API functions
export async function fetchNotifications(params: {
  limit?: number
  offset?: number
  notification_type?: string
  severity?: string
  is_read?: boolean
  days_back?: number
} = {}) {
  try {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, value.toString())
      }
    })
    
    const resp = await fetch(`${API_BASE}/notifications/notifications?${searchParams}`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to fetch notifications:', error)
    return []
  }
}

export async function fetchUnreadNotificationCount() {
  try {
    const resp = await fetch(`${API_BASE}/notifications/unread-count`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to fetch unread notification count:', error)
    return { unread_count: 0 }
  }
}

export async function markNotificationAsRead(notificationId: number) {
  try {
    const resp = await fetch(`${API_BASE}/notifications/notifications/${notificationId}/read`, {
      method: 'PUT'
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to mark notification as read:', error)
    return { success: false }
  }
}

export async function markAllNotificationsAsRead() {
  try {
    const resp = await fetch(`${API_BASE}/notifications/mark-all-read`, {
      method: 'PUT'
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to mark all notifications as read:', error)
    return { success: false }
  }
}

export async function acknowledgeNotification(notificationId: number, acknowledgedBy: string = 'user') {
  try {
    const resp = await fetch(`${API_BASE}/notifications/notifications/${notificationId}/acknowledge?acknowledged_by=${acknowledgedBy}`, {
      method: 'PUT'
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to acknowledge notification:', error)
    return { success: false }
  }
}

export async function fetchNotificationStats(daysBack: number = 7) {
  try {
    const resp = await fetch(`${API_BASE}/notifications/notifications/stats?days_back=${daysBack}`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to fetch notification stats:', error)
    return {}
  }
}

export async function createTestNotification(notificationType: string = 'info', title: string = 'Test Notification', message: string = 'This is a test notification', severity: string = 'info') {
  try {
    const resp = await fetch(`${API_BASE}/notifications/test?notification_type=${notificationType}&title=${encodeURIComponent(title)}&message=${encodeURIComponent(message)}&severity=${severity}`, {
      method: 'POST'
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
  } catch (error) {
    console.error('Failed to create test notification:', error)
    return { success: false }
  }
}


