import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from './App'

// Mock the API module
vi.mock('./api', () => ({
  fetchDevices: vi.fn().mockResolvedValue([
    { id: 'dev1', hostname: 'Test Device', mgmt_ip: '192.168.1.100', vendor: 'Test Vendor', model: 'Test Model', status: 'online' }
  ]),
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
  fetchDeviceHistory: vi.fn().mockResolvedValue([]),
  fetchDeviceSessionStats: vi.fn().mockResolvedValue({}),
  fetchRecentEvents: vi.fn().mockResolvedValue([]),
  fetchGroupedDevices: vi.fn().mockResolvedValue({}),
  fetchGroupingStats: vi.fn().mockResolvedValue({}),
  getUnknownVendors: vi.fn().mockResolvedValue([]),
  getNetworkStatus: vi.fn().mockResolvedValue({ connected: true, error: null }),
  fetchNotifications: vi.fn().mockResolvedValue([
    {
      id: 1,
      notification_type: 'new_device',
      title: 'New Device Detected',
      message: 'A new device "Test Device" (192.168.1.100) from Test Vendor has joined the network',
      device_id: 'dev1',
      severity: 'info',
      is_read: false,
      is_acknowledged: false,
      created_at: '2024-01-01T10:00:00Z',
      acknowledged_at: null,
      acknowledged_by: null,
      notification_data: {}
    }
  ]),
  fetchUnreadNotificationCount: vi.fn().mockResolvedValue({ unread_count: 1 }),
  markNotificationAsRead: vi.fn().mockResolvedValue({ success: true }),
  markAllNotificationsAsRead: vi.fn().mockResolvedValue({ success: true }),
  acknowledgeNotification: vi.fn().mockResolvedValue({ success: true }),
  fetchNotificationStats: vi.fn().mockResolvedValue({
    total_notifications: 1,
    unread_notifications: 1,
    by_type: { new_device: 1 },
    by_severity: { info: 1 },
    period_days: 7
  }),
  createTestNotification: vi.fn().mockResolvedValue({ success: true }),
  deleteNotification: vi.fn().mockResolvedValue({ success: true }),
  clearAllNotifications: vi.fn().mockResolvedValue({ success: true })
}))

describe('Notification System - Core Functionality', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.clearAllTimers()
  })

  afterEach(() => {
    vi.clearAllTimers()
    document.body.innerHTML = ''
  })

  it('renders notification bell with unread count', async () => {
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    // Check that unread count is displayed - just check for any "1" text
    const unreadBadges = screen.getAllByText('1')
    expect(unreadBadges.length).toBeGreaterThan(0)
  })

  it('opens notification panel when bell is clicked', async () => {
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0]
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      expect(screen.getByText('🔔 Notifications')).toBeInTheDocument()
    })
  })

  it('displays notification statistics', async () => {
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0]
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      // Check if the notification panel opened
      const panelTitle = screen.queryByText('🔔 Notifications')
      const hasPanel = panelTitle !== null
      expect(hasPanel).toBeTruthy()
    })
    
    // Check statistics are displayed - just verify the labels exist
    expect(screen.getByText('Total:')).toBeInTheDocument()
    expect(screen.getByText('Unread:')).toBeInTheDocument()
    expect(screen.getByText('Info:')).toBeInTheDocument()
    expect(screen.getByText('Warning:')).toBeInTheDocument()
    expect(screen.getByText('Critical:')).toBeInTheDocument()
    expect(screen.getByText('Period:')).toBeInTheDocument()
  })

  it('calls API functions when panel opens', async () => {
    const { fetchNotifications, fetchNotificationStats } = await import('./api')
    
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0]
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      expect(screen.getByText('🔔 Notifications')).toBeInTheDocument()
    })
    
    // Verify API functions were called
    expect(fetchNotifications).toHaveBeenCalledWith({ limit: 50, days_back: 7 })
    expect(fetchNotificationStats).toHaveBeenCalledWith(7)
  })
})
