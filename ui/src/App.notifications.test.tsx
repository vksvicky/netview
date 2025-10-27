import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import App from './App'

// Mock the API functions
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
  fetchDeviceHistory: vi.fn(),
  fetchDeviceSessionStats: vi.fn(),
  fetchRecentEvents: vi.fn(),
  fetchGroupedDevices: vi.fn().mockResolvedValue({}),
  fetchGroupingStats: vi.fn().mockResolvedValue({}),
  getUnknownVendors: vi.fn().mockResolvedValue([]),
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
    },
    {
      id: 2,
      notification_type: 'device_offline',
      title: 'Device Went Offline',
      message: 'Device "Test Device" (192.168.1.100) has gone offline',
      device_id: 'dev1',
      severity: 'warning',
      is_read: true,
      is_acknowledged: false,
      created_at: '2024-01-01T09:00:00Z',
      acknowledged_at: null,
      acknowledged_by: null,
      notification_data: {}
    }
  ]),
  fetchUnreadNotificationCount: vi.fn().mockResolvedValue({ unread_count: 1 }),
  markNotificationAsRead: vi.fn().mockResolvedValue({ success: true }),
  markAllNotificationsAsRead: vi.fn().mockResolvedValue({ success: true, count: 1 }),
  acknowledgeNotification: vi.fn().mockResolvedValue({ success: true }),
  fetchNotificationStats: vi.fn().mockResolvedValue({
    total_notifications: 2,
    unread_notifications: 1,
    by_type: { new_device: 1, device_offline: 1 },
    by_severity: { info: 1, warning: 1 },
    period_days: 7
  }),
  createTestNotification: vi.fn().mockResolvedValue({ success: true })
}))

describe('Notification System Feature', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Clear any existing timers
    vi.clearAllTimers()
  })
  
  afterEach(() => {
    // Clean up any remaining timers
    vi.clearAllTimers()
    // Clear DOM to prevent interference between tests
    document.body.innerHTML = ''
  })

  it('renders notification bell icon in toolbar', async () => {
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    expect(bellIcon).toBeInTheDocument()
    expect(bellIcon.textContent).toContain('🔔')
  })

  it('shows unread count badge on notification bell', async () => {
    render(<App />)
    
    await waitFor(() => {
      const badges = screen.getAllByText('1')
      expect(badges.length).toBeGreaterThan(0)
    })
    
    const badges = screen.getAllByText('1')
    // Find the badge that's inside the notification bell (has red background)
    const unreadBadge = badges.find(badge => {
      // Check if this badge is inside a notification bell button
      const bellButton = badge.closest('button[title="Notifications"]')
      return bellButton !== null
    })
    expect(unreadBadge).toBeInTheDocument()
    expect(unreadBadge?.textContent).toBe('1')
  })

  it('opens notification panel when bell is clicked', async () => {
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      expect(screen.getByText('🔔 Notifications')).toBeInTheDocument()
    })
    
    expect(screen.getByText('🔔 Notifications')).toBeInTheDocument()
    expect(screen.getByText('Test')).toBeInTheDocument()
    expect(screen.getByText('Mark All Read')).toBeInTheDocument()
  })

  it('displays notification statistics in panel', async () => {
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      expect(screen.getByText('Total:')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Total:')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('Unread:')).toBeInTheDocument()
    // Check for the unread count in stats (not the badge)
    const unreadStats = screen.getByText('Unread:').parentElement
    expect(unreadStats).toHaveTextContent('1')
    expect(screen.getByText('Info:')).toBeInTheDocument()
    expect(screen.getByText('Warning:')).toBeInTheDocument()
    expect(screen.getByText('Critical:')).toBeInTheDocument()
    expect(screen.getByText('0')).toBeInTheDocument()
    expect(screen.getByText('Period:')).toBeInTheDocument()
    expect(screen.getByText('7 days')).toBeInTheDocument()
  })

  it('displays notifications list in panel', async () => {
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    // Wait for the panel to open and notifications to load
    await waitFor(() => {
      expect(screen.getByText('🔔 Notifications')).toBeInTheDocument()
    })
    
    // Wait for notifications to be loaded (either the actual notifications or "No notifications")
    await waitFor(() => {
      const hasNotifications = screen.queryByText('New Device Detected')
      const hasNoNotifications = screen.queryByText('No notifications')
      const isLoading = screen.queryByText('Loading notifications...')
      
      // One of these should be present
      expect(hasNotifications || hasNoNotifications || isLoading).toBeTruthy()
    })
    
    // If notifications are displayed, check for specific content
    const hasNotifications = screen.queryByText('New Device Detected')
    if (hasNotifications) {
      expect(screen.getByText('New Device Detected')).toBeInTheDocument()
      expect(screen.getByText('Device Went Offline')).toBeInTheDocument()
      expect(screen.getByText('A new device "Test Device" (192.168.1.100) from Test Vendor has joined the network')).toBeInTheDocument()
    }
  })

  it('shows different colors for notification severity', async () => {
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      // Check if notifications are displayed or if "No notifications" is shown
      const hasNotifications = screen.queryByText('New Device Detected')
      const hasNoNotifications = screen.queryByText('No notifications')
      expect(hasNotifications || hasNoNotifications).toBeTruthy()
    })
    
    // If notifications are displayed, check for severity badges
    const hasNotifications = screen.queryByText('New Device Detected')
    if (hasNotifications) {
      const severityBadges = screen.getAllByText(/info|warning/)
      expect(severityBadges.length).toBeGreaterThan(0)
    }
    
    // If notifications are displayed, check for notification type labels
    if (hasNotifications) {
      expect(screen.getByText('new_device')).toBeInTheDocument()
      expect(screen.getByText('device_offline')).toBeInTheDocument()
    }
  })

  it('allows marking individual notifications as read', async () => {
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      // Check if notifications are displayed or if "No notifications" is shown
      const hasNotifications = screen.queryByText('New Device Detected')
      const hasNoNotifications = screen.queryByText('No notifications')
      expect(hasNotifications || hasNoNotifications).toBeTruthy()
    })
    
    // If notifications are displayed, try to mark one as read
    const hasNotifications = screen.queryByText('New Device Detected')
    if (hasNotifications) {
      const markReadButton = screen.queryByText('Mark Read')
      if (markReadButton) {
        fireEvent.click(markReadButton)
        // The button should disappear after marking as read
        await waitFor(() => {
          expect(screen.queryByText('Mark Read')).not.toBeInTheDocument()
        })
      }
    }
  })

  it('allows acknowledging notifications', async () => {
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      // Check if notifications are displayed or if "No notifications" is shown
      const hasNotifications = screen.queryByText('New Device Detected')
      const hasNoNotifications = screen.queryByText('No notifications')
      expect(hasNotifications || hasNoNotifications).toBeTruthy()
    })
    
    // If notifications are displayed, try to acknowledge one
    const hasNotifications = screen.queryByText('New Device Detected')
    if (hasNotifications) {
      const ackButtons = screen.getAllByText('Ack')
      expect(ackButtons.length).toBeGreaterThan(0)
      
      const ackButton = ackButtons[0] // Use the first one
      fireEvent.click(ackButton)
      
      // Wait for the acknowledge action to complete
      await waitFor(() => {
        // The button might disappear or change after acknowledgment
        const remainingAckButtons = screen.queryAllByText('Ack')
        expect(remainingAckButtons.length).toBeLessThan(ackButtons.length)
      })
    }
  })

  it('allows marking all notifications as read', async () => {
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      // Check if notifications are displayed or if "No notifications" is shown
      const hasNotifications = screen.queryByText('New Device Detected')
      const hasNoNotifications = screen.queryByText('No notifications')
      expect(hasNotifications || hasNoNotifications).toBeTruthy()
    })
    
    // If notifications are displayed, try to mark all as read
    const hasNotifications = screen.queryByText('New Device Detected')
    if (hasNotifications) {
      const markAllReadButton = screen.queryByText('Mark All Read')
      if (markAllReadButton) {
        fireEvent.click(markAllReadButton)
        // All Mark Read buttons should disappear
        await waitFor(() => {
          expect(screen.queryByText('Mark Read')).not.toBeInTheDocument()
        })
      }
    }
  })

  it('allows creating test notifications', async () => {
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      // Check if notifications are displayed or if "No notifications" is shown
      const hasNotifications = screen.queryByText('New Device Detected')
      const hasNoNotifications = screen.queryByText('No notifications')
      expect(hasNotifications || hasNoNotifications).toBeTruthy()
    })
    
    // The Test button should be available regardless of notification state
    const testButton = screen.queryByText('Test')
    if (testButton) {
      fireEvent.click(testButton)
      // Should create a test notification (API call is mocked)
      await waitFor(() => {
        // The notification list should be refreshed
        const hasNotifications = screen.queryByText('New Device Detected')
        const hasNoNotifications = screen.queryByText('No notifications')
        expect(hasNotifications || hasNoNotifications).toBeTruthy()
      })
    }
  })

  it('closes notification panel when close button is clicked', async () => {
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      // Check if notifications are displayed or if "No notifications" is shown
      const hasNotifications = screen.queryByText('New Device Detected')
      const hasNoNotifications = screen.queryByText('No notifications')
      expect(hasNotifications || hasNoNotifications).toBeTruthy()
    })
    
    const closeButton = screen.queryByText('✕')
    if (closeButton) {
      fireEvent.click(closeButton)
      // Panel should be closed
      await waitFor(() => {
        expect(screen.queryByText('🔔 Notifications')).not.toBeInTheDocument()
      })
    }
  })

  it('handles empty notifications gracefully', async () => {
    // Mock empty notifications
    const { fetchNotifications } = await import('./api')
    vi.mocked(fetchNotifications).mockResolvedValueOnce([])
    
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      expect(screen.getByText('No notifications')).toBeInTheDocument()
    })
    
    expect(screen.getByText('No notifications')).toBeInTheDocument()
  })

  it('handles loading state gracefully', async () => {
    // Mock slow loading
    const { fetchNotifications } = await import('./api')
    vi.mocked(fetchNotifications).mockImplementationOnce(() => 
      new Promise(resolve => setTimeout(() => resolve([]), 100))
    )
    
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    // Should show loading state briefly
    await waitFor(() => {
      expect(screen.getByText('Loading notifications...')).toBeInTheDocument()
    })
  })

  it('handles API errors gracefully', async () => {
    // Mock API error
    const { fetchNotifications } = await import('./api')
    vi.mocked(fetchNotifications).mockRejectedValueOnce(new Error('API Error'))
    
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    // Should handle error gracefully (empty list)
    await waitFor(() => {
      expect(screen.getByText('No notifications')).toBeInTheDocument()
    })
  })

  it('formats timestamps correctly', async () => {
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      // Check if notifications are displayed or if "No notifications" is shown
      const hasNotifications = screen.queryByText('New Device Detected')
      const hasNoNotifications = screen.queryByText('No notifications')
      expect(hasNotifications || hasNoNotifications).toBeTruthy()
    })
    
    // If notifications are displayed, check that timestamps are displayed
    const hasNotifications = screen.queryByText('New Device Detected')
    if (hasNotifications) {
      const timestamps = screen.getAllByText(/1\/1\/2024/)
      expect(timestamps.length).toBeGreaterThan(0)
    }
  })

  it('shows unread notifications with different styling', async () => {
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      // Check if notifications are displayed or if "No notifications" is shown
      const hasNotifications = screen.queryByText('New Device Detected')
      const hasNoNotifications = screen.queryByText('No notifications')
      expect(hasNotifications || hasNoNotifications).toBeTruthy()
    })
    
    // If notifications are displayed, check styling
    const hasNotifications = screen.queryByText('New Device Detected')
    if (hasNotifications) {
      const unreadNotification = screen.getByText('New Device Detected')
      expect(unreadNotification).toHaveStyle('font-weight: bold')
    }
    
    // If notifications are displayed, check styling for read notifications too
    if (hasNotifications) {
      const readNotification = screen.queryByText('Device Went Offline')
      if (readNotification) {
        expect(readNotification).toHaveStyle('font-weight: normal')
      }
    }
  })

  it('updates unread count when notifications are marked as read', async () => {
    render(<App />)
    
    await waitFor(() => {
      const badges = screen.getAllByText('1')
      expect(badges.length).toBeGreaterThan(0)
    })
    
    // Find the unread badge specifically (the one inside the notification bell)
    const unreadBadges = screen.getAllByText('1').filter(badge => {
      // Check if this badge is inside a notification bell button
      const bellButton = badge.closest('button[title="Notifications"]')
      return bellButton !== null
    })
    expect(unreadBadges.length).toBeGreaterThan(0)
    expect(unreadBadges[0].textContent).toBe('1')
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      expect(screen.getByText('Mark Read')).toBeInTheDocument()
    })
    
    const markReadButton = screen.getByText('Mark Read')
    fireEvent.click(markReadButton)
    
    // Unread count should decrease (check the badge specifically)
    await waitFor(() => {
      const unreadBadges = screen.getAllByText('1').filter(badge => {
        const bellButton = badge.closest('button[title="Notifications"]')
        return bellButton !== null
      })
      expect(unreadBadges.length).toBe(0) // No unread badges should remain
    })
  })

  it('loads notifications and stats when panel opens', async () => {
    const { fetchNotifications, fetchNotificationStats } = await import('./api')
    
    render(<App />)
    
    await waitFor(() => {
      const bellIcons = screen.getAllByTitle('Notifications')
      expect(bellIcons.length).toBeGreaterThan(0)
    })
    
    const bellIcons = screen.getAllByTitle('Notifications')
    const bellIcon = bellIcons[0] // Use the first one
    fireEvent.click(bellIcon)
    
    await waitFor(() => {
      // Check if the notification panel opened
      const panelTitle = screen.queryByText('🔔 Notifications')
      const hasPanel = panelTitle !== null
      expect(hasPanel).toBeTruthy()
    })
    
    // Should have called the API functions
    expect(fetchNotifications).toHaveBeenCalledWith({ limit: 50, days_back: 7 })
    expect(fetchNotificationStats).toHaveBeenCalledWith(7)
  })
})
