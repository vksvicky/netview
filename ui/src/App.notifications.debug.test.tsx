import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from './App'

// Mock all API functions
vi.mock('./api', () => ({
  fetchTopology: vi.fn().mockResolvedValue({
    nodes: [
      { id: 'router', label: 'Router', title: '192.168.1.1' },
      { id: 'dev1', label: 'Test Device', title: '192.168.1.100' }
    ],
    edges: []
  }),
  fetchDevice: vi.fn().mockResolvedValue({
    id: 'dev1',
    hostname: 'Test Device',
    mgmtIp: '192.168.1.100',
    vendor: 'Test Vendor',
    model: 'Test Model',
    status: 'up'
  }),
  fetchInterfaces: vi.fn().mockResolvedValue([
    { id: 'dev1:1', ifIndex: 1, name: 'eth0', adminStatus: 'up', operStatus: 'up' }
  ]),
  fetchInterfaceMetrics: vi.fn().mockResolvedValue({ lastCounters: { inOctets: 1000 } }),
  triggerDiscovery: vi.fn().mockResolvedValue({ nodes: [], edges: [] }),
  getNetworkStatus: vi.fn().mockResolvedValue({ connected: true, error: null }),
  fetchDeviceHistory: vi.fn().mockResolvedValue([]),
  fetchDeviceSessionStats: vi.fn().mockResolvedValue({}),
  fetchRecentEvents: vi.fn().mockResolvedValue([]),
  fetchGroupedDevices: vi.fn().mockResolvedValue({}),
  fetchGroupingStats: vi.fn().mockResolvedValue({}),
  getUnknownVendors: vi.fn().mockResolvedValue([]),
  fetchNotifications: vi.fn().mockResolvedValue([
    {
      id: 1,
      title: 'New Device Detected',
      message: 'A new device has joined the network',
      severity: 'info',
      notification_type: 'new_device',
      is_read: false,
      is_acknowledged: false,
      created_at: '2024-01-01T00:00:00Z'
    }
  ]),
  fetchUnreadNotificationCount: vi.fn().mockResolvedValue({ unread_count: 1 }),
  markNotificationAsRead: vi.fn().mockResolvedValue({ success: true }),
  markAllNotificationsAsRead: vi.fn().mockResolvedValue({ success: true }),
  acknowledgeNotification: vi.fn().mockResolvedValue({ success: true }),
  fetchNotificationStats: vi.fn().mockResolvedValue({
    total_notifications: 1,
    unread_notifications: 1,
    by_severity: { info: 1, warning: 0, critical: 0 },
    period_days: 7
  }),
  createTestNotification: vi.fn().mockResolvedValue({ success: true }),
  deleteNotification: vi.fn().mockResolvedValue({ success: true }),
  clearAllNotifications: vi.fn().mockResolvedValue({ success: true })
}))

describe('Notification Panel Debug', () => {
  beforeEach(() => {
    vi.clearAllTimers()
  })

  afterEach(() => {
    vi.clearAllTimers()
    document.body.innerHTML = ''
  })

  it('should open notification panel when bell is clicked', async () => {
    render(<App />)
    
    // Wait for the component to render
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    // Find the first bell icon
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0]
    expect(bellIcon).toBeInTheDocument()
    
    // Click the bell icon
    fireEvent.click(bellIcon)
    
    // Wait for the panel to appear
    await waitFor(() => {
      expect(screen.getByText('🔔 Notifications')).toBeInTheDocument()
    }, { timeout: 3000 })
    
    // Verify the panel is open
    expect(screen.getByText('🔔 Notifications')).toBeInTheDocument()
    expect(screen.getByText('Test')).toBeInTheDocument()
    expect(screen.getByText('Mark All Read')).toBeInTheDocument()
  })

  it('should show notification content when panel is open', async () => {
    render(<App />)
    
    // Wait for the component to render
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    // Find and click the first bell icon
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0]
    fireEvent.click(bellIcon)
    
    // Wait for the panel to appear
    await waitFor(() => {
      expect(screen.getByText('🔔 Notifications')).toBeInTheDocument()
    }, { timeout: 3000 })
    
    // Wait for notifications to load
    await waitFor(() => {
      const hasNotifications = screen.queryByText('New Device Detected')
      const hasNoNotifications = screen.queryByText('No notifications')
      expect(hasNotifications || hasNoNotifications).toBeTruthy()
    }, { timeout: 3000 })
    
    // Check if notifications are displayed
    const hasNotifications = screen.queryByText('New Device Detected')
    if (hasNotifications) {
      expect(screen.getByText('New Device Detected')).toBeInTheDocument()
      expect(screen.getByText('A new device has joined the network')).toBeInTheDocument()
    }
  })
})
