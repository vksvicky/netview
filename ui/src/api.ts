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


