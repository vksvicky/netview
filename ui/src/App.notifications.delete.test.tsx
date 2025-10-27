import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from './App'

// Mock all API functions
vi.mock('./api', () => ({
  getNetworkStatus: vi.fn().mockResolvedValue({ status: 'online', devices: 5 }),
  fetchTopology: vi.fn().mockResolvedValue({ nodes: [], edges: [] }),
  fetchDevice: vi.fn().mockResolvedValue({}),
  fetchInterfaces: vi.fn().mockResolvedValue([]),
  fetchInterfaceMetrics: vi.fn().mockResolvedValue([]),
  triggerDiscovery: vi.fn().mockResolvedValue({ success: true }),
  fetchDeviceHistory: vi.fn().mockResolvedValue([]),
  fetchDeviceSessionStats: vi.fn().mockResolvedValue({}),
  fetchRecentEvents: vi.fn().mockResolvedValue([]),
  fetchGroupedDevices: vi.fn().mockResolvedValue({}),
  fetchGroupingStats: vi.fn().mockResolvedValue({}),
  getUnknownVendors: vi.fn().mockResolvedValue([]),
  fetchNotifications: vi.fn().mockResolvedValue([
    {
      id: 1,
      title: 'Test Notification 1',
      message: 'This is a test notification',
      severity: 'info',
      notification_type: 'new_device',
      is_read: false,
      is_acknowledged: false,
      created_at: '2025-10-27T17:00:00Z'
    },
    {
      id: 2,
      title: 'Test Notification 2',
      message: 'This is another test notification',
      severity: 'warning',
      notification_type: 'device_offline',
      is_read: true,
      is_acknowledged: false,
      created_at: '2025-10-27T17:01:00Z'
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
  createTestNotification: vi.fn().mockResolvedValue({ success: true }),
  deleteNotification: vi.fn().mockResolvedValue({ success: true }),
  clearAllNotifications: vi.fn().mockResolvedValue({ success: true, count: 2 })
}))

describe('Notification Delete Functionality', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.clearAllTimers()
  })

  afterEach(() => {
    vi.clearAllTimers()
    document.body.innerHTML = ''
  })

  it('displays delete button for each notification', async () => {
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
    
    // Wait for notifications to load
    await waitFor(() => {
      expect(screen.getByText('Test Notification 1')).toBeInTheDocument()
    })
    
    // Check that delete buttons are present
    const deleteButtons = screen.getAllByText('Delete')
    expect(deleteButtons.length).toBe(2) // One for each notification
  })

  it('calls deleteNotification API when delete button is clicked', async () => {
    const { deleteNotification } = await import('./api')
    
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
    
    await waitFor(() => {
      expect(screen.getByText('Test Notification 1')).toBeInTheDocument()
    })
    
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])
    
    await waitFor(() => {
      expect(deleteNotification).toHaveBeenCalledWith(1)
    })
  })

  it('removes notification from UI after successful deletion', async () => {
    const { deleteNotification } = await import('./api')
    
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
    
    await waitFor(() => {
      expect(screen.getByText('Test Notification 1')).toBeInTheDocument()
    })
    
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])
    
    // The notification should be removed from the UI
    await waitFor(() => {
      expect(screen.queryByText('Test Notification 1')).not.toBeInTheDocument()
    })
  })

  it('displays clear all button in notification panel header', async () => {
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
    
    // Check that clear all button is present
    expect(screen.getByText('Clear All')).toBeInTheDocument()
  })

  it('calls clearAllNotifications API when clear all button is clicked', async () => {
    const { clearAllNotifications } = await import('./api')
    
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
    
    const clearAllButton = screen.getByText('Clear All')
    fireEvent.click(clearAllButton)
    
    await waitFor(() => {
      expect(clearAllNotifications).toHaveBeenCalled()
    })
  })

  it('clears all notifications from UI after successful clear all', async () => {
    const { clearAllNotifications } = await import('./api')
    
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
    
    await waitFor(() => {
      expect(screen.getByText('Test Notification 1')).toBeInTheDocument()
    })
    
    const clearAllButton = screen.getByText('Clear All')
    fireEvent.click(clearAllButton)
    
    // All notifications should be removed from the UI
    await waitFor(() => {
      expect(screen.queryByText('Test Notification 1')).not.toBeInTheDocument()
      expect(screen.queryByText('Test Notification 2')).not.toBeInTheDocument()
    })
  })

  it('updates unread count after deleting notifications', async () => {
    const { deleteNotification, fetchUnreadNotificationCount } = await import('./api')
    
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
    
    await waitFor(() => {
      expect(screen.getByText('Test Notification 1')).toBeInTheDocument()
    })
    
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])
    
    // Should reload unread count after deletion
    await waitFor(() => {
      expect(fetchUnreadNotificationCount).toHaveBeenCalled()
    })
  })

  it('handles delete notification API errors gracefully', async () => {
    const { deleteNotification } = await import('./api')
    deleteNotification.mockRejectedValueOnce(new Error('Delete failed'))
    
    // Mock console.error to avoid error logs in test output
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    
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
    
    await waitFor(() => {
      expect(screen.getByText('Test Notification 1')).toBeInTheDocument()
    })
    
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])
    
    // Should handle error gracefully
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to delete notification:', expect.any(Error))
    })
    
    consoleSpy.mockRestore()
  })

  it('handles clear all notifications API errors gracefully', async () => {
    const { clearAllNotifications } = await import('./api')
    clearAllNotifications.mockRejectedValueOnce(new Error('Clear all failed'))
    
    // Mock console.error to avoid error logs in test output
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    
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
    
    const clearAllButton = screen.getByText('Clear All')
    fireEvent.click(clearAllButton)
    
    // Should handle error gracefully
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to clear all notifications:', expect.any(Error))
    })
    
    consoleSpy.mockRestore()
  })
})
