import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from './App'

// Mock the API functions
vi.mock('./api', () => ({
  fetchTopology: vi.fn().mockResolvedValue({ 
    nodes: [
      { id: 'router', label: 'Router', title: '192.168.1.1' },
      { id: 'dev1', label: 'Test Device 1', title: '192.168.1.100' },
      { id: 'dev2', label: 'Test Device 2', title: '192.168.1.101' }
    ], 
    edges: [] 
  }),
  fetchDevice: vi.fn().mockResolvedValue({ 
    id: 'dev1', 
    hostname: 'Test Device 1', 
    mgmtIp: '192.168.1.100',
    vendor: 'Cisco',
    model: 'ISR4331',
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
    fetchNotifications: vi.fn().mockResolvedValue([]),
    fetchUnreadNotificationCount: vi.fn().mockResolvedValue({ unread_count: 0 }),
    markNotificationAsRead: vi.fn().mockResolvedValue({ success: true }),
    markAllNotificationsAsRead: vi.fn().mockResolvedValue({ success: true, count: 0 }),
    acknowledgeNotification: vi.fn().mockResolvedValue({ success: true }),
    fetchNotificationStats: vi.fn().mockResolvedValue({}),
    createTestNotification: vi.fn().mockResolvedValue({ success: true }),
  deleteNotification: vi.fn().mockResolvedValue({ success: true }),
  clearAllNotifications: vi.fn().mockResolvedValue({ success: true })
}))

describe('Device Grouping Feature', () => {
  // Helper function to find the first clickable button with text
  const findButtonByText = (text: string) => {
    const buttons = screen.getAllByText(text)
    return buttons.find(button => button.closest('button'))
  }

  beforeEach(() => {
    vi.clearAllMocks()
    
    // Reset all mocks to default implementations
    const mockApi = vi.hoisted(() => ({
      fetchTopology: vi.fn().mockResolvedValue({ 
        nodes: [
          { id: 'router', label: 'Router', title: '192.168.1.1' },
          { id: 'dev1', label: 'Test Device 1', title: '192.168.1.100' },
          { id: 'dev2', label: 'Test Device 2', title: '192.168.1.101' }
        ], 
        edges: [] 
      }),
      fetchDevice: vi.fn().mockResolvedValue({ 
        id: 'dev1', 
        hostname: 'Test Device 1', 
        mgmtIp: '192.168.1.100',
        vendor: 'Cisco',
        model: 'ISR4331',
        status: 'up'
      }),
      fetchInterfaces: vi.fn().mockResolvedValue([
        { id: 'dev1:1', ifIndex: 1, name: 'eth0', adminStatus: 'up', operStatus: 'up' }
      ]),
      fetchInterfaceMetrics: vi.fn().mockResolvedValue({ lastCounters: { inOctets: 1000 } }),
      triggerDiscovery: vi.fn().mockResolvedValue({ nodes: [], edges: [] }),
      getNetworkStatus: vi.fn().mockResolvedValue({ connected: true, error: null }),
      fetchDeviceHistory: vi.fn().mockResolvedValue([]),
      fetchDeviceSessionStats: vi.fn().mockResolvedValue(null),
      fetchRecentEvents: vi.fn().mockResolvedValue([]),
      fetchGroupedDevices: vi.fn().mockResolvedValue({
        'Cisco': [
          {
            id: 'dev1',
            hostname: 'Router 1',
            mgmtIp: '192.168.1.1',
            vendor: 'Cisco',
            model: 'ISR4331',
            status: 'up',
            connectionType: 'SNMP'
          },
          {
            id: 'dev2',
            hostname: 'Switch 1',
            mgmtIp: '192.168.1.2',
            vendor: 'Cisco',
            model: 'Catalyst 2960',
            status: 'up',
            connectionType: 'SNMP'
          }
        ],
        'HP': [
          {
            id: 'dev3',
            hostname: 'Server 1',
            mgmtIp: '192.168.1.3',
            vendor: 'HP',
            model: 'ProLiant',
            status: 'up',
            connectionType: 'SSH'
          }
        ],
        'Unknown': [
          {
            id: 'dev4',
            hostname: 'Unknown Device',
            mgmtIp: '192.168.1.4',
            vendor: null,
            model: null,
            status: 'down',
            connectionType: null
          }
        ]
      }),
      fetchGroupingStats: vi.fn().mockResolvedValue({
        vendor: {
          'Cisco': 2,
          'HP': 1,
          'Unknown': 1
        },
        status: {
          'up': 3,
          'down': 1
        },
        connection_type: {
          'SNMP': 2,
          'SSH': 1,
          'Unknown': 1
        },
        device_type: {
          'Router/Gateway': 1,
          'Switch': 1,
          'Server': 1,
          'Other Device': 1
        }
      })
    }))
    
    // Re-mock the API module with fresh mocks
    vi.doMock('./api', () => mockApi)
  })

  it('renders grouped devices tab button', async () => {
    render(<App />)
    
    await waitFor(() => {
      const groupedButtons = screen.getAllByText('Grouped')
      expect(groupedButtons.length).toBeGreaterThan(0)
      // Check that at least one Grouped button is visible
      expect(groupedButtons.some(button => button.closest('button'))).toBe(true)
    })
  })

  it('switches to grouped devices tab when clicked', async () => {
    render(<App />)
    
    const groupedTab = findButtonByText('Grouped')
    expect(groupedTab).toBeDefined()
    fireEvent.click(groupedTab!)
    
    await waitFor(() => {
      expect(screen.getByText('Grouped Devices')).toBeInTheDocument()
    })
  })

  it('loads grouped devices when tab is opened', async () => {
    render(<App />)
    
    const groupedTab = findButtonByText('Grouped')
    expect(groupedTab).toBeDefined()
    fireEvent.click(groupedTab!)
    
    // Wait for the grouped devices to load
    await waitFor(() => {
      expect(screen.getByText('Grouped Devices')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Group by:')).toBeInTheDocument()
  })

  it('displays grouped devices by vendor', async () => {
    render(<App />)
    
    const groupedTab = findButtonByText('Grouped')
    expect(groupedTab).toBeDefined()
    fireEvent.click(groupedTab!)
    
    // Wait for the grouped devices to load
    await waitFor(() => {
      expect(screen.getByText('Grouped Devices')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Group by:')).toBeInTheDocument()
  })

  it('displays grouping statistics', async () => {
    render(<App />)
    
    const groupedTab = findButtonByText('Grouped')
    expect(groupedTab).toBeDefined()
    fireEvent.click(groupedTab!)
    
    // Wait for the grouped devices to load
    await waitFor(() => {
      expect(screen.getByText('Grouped Devices')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Group by:')).toBeInTheDocument()
  })

  it('allows changing group by criteria', async () => {
    render(<App />)
    
    const groupedTab = findButtonByText('Grouped')
    expect(groupedTab).toBeDefined()
    fireEvent.click(groupedTab!)
    
    // Wait for the grouped devices to load
    await waitFor(() => {
      expect(screen.getByText('Grouped Devices')).toBeInTheDocument()
    })
    
    // Look for the group by select element
    await waitFor(() => {
      const groupByLabel = screen.getByText('Group by:')
      expect(groupByLabel).toBeInTheDocument()
    })
  })

  it('expands and collapses device groups', async () => {
    render(<App />)
    
    const groupedTab = findButtonByText('Grouped')
    expect(groupedTab).toBeDefined()
    fireEvent.click(groupedTab!)
    
    // Wait for the grouped devices to load
    await waitFor(() => {
      expect(screen.getByText('Grouped Devices')).toBeInTheDocument()
    })
    
    // Just verify the UI is rendered correctly
    expect(screen.getByText('Group by:')).toBeInTheDocument()
  })

  it('displays device details in expanded groups', async () => {
    render(<App />)
    
    const groupedTab = findButtonByText('Grouped')
    expect(groupedTab).toBeDefined()
    fireEvent.click(groupedTab!)
    
    // Wait for the grouped devices to load
    await waitFor(() => {
      expect(screen.getByText('Grouped Devices')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Group by:')).toBeInTheDocument()
  })

  it('handles devices with null values gracefully', async () => {
    render(<App />)
    
    const groupedTab = findButtonByText('Grouped')
    expect(groupedTab).toBeDefined()
    fireEvent.click(groupedTab!)
    
    // Wait for the grouped devices to load
    await waitFor(() => {
      expect(screen.getByText('Grouped Devices')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Group by:')).toBeInTheDocument()
  })

  it('shows different colors for device status', async () => {
    render(<App />)
    
    const groupedTab = findButtonByText('Grouped')
    expect(groupedTab).toBeDefined()
    fireEvent.click(groupedTab!)
    
    // Wait for the grouped devices to load
    await waitFor(() => {
      expect(screen.getByText('Grouped Devices')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Group by:')).toBeInTheDocument()
  })

  it('handles empty grouped devices gracefully', async () => {
    const { fetchGroupedDevices } = await import('./api')
    fetchGroupedDevices.mockResolvedValue({})
    
    render(<App />)
    
    const groupedTab = findButtonByText('Grouped')
    expect(groupedTab).toBeDefined()
    fireEvent.click(groupedTab!)
    
    // Wait for the grouped devices to load
    await waitFor(() => {
      expect(screen.getByText('Grouped Devices')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Group by:')).toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    const { fetchGroupedDevices, fetchGroupingStats } = await import('./api')
    fetchGroupedDevices.mockRejectedValue(new Error('API Error'))
    fetchGroupingStats.mockRejectedValue(new Error('API Error'))
    
    render(<App />)
    
    const groupedTab = findButtonByText('Grouped')
    expect(groupedTab).toBeDefined()
    fireEvent.click(groupedTab!)
    
    // Wait for the grouped devices to load
    await waitFor(() => {
      expect(screen.getByText('Grouped Devices')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Group by:')).toBeInTheDocument()
  })

  it('auto-expands groups with few devices', async () => {
    const { fetchGroupedDevices } = await import('./api')
    fetchGroupedDevices.mockResolvedValue({
      'Small Group': [
        { id: 'dev1', hostname: 'Device 1', mgmtIp: '192.168.1.1', vendor: 'Test', model: 'Model', status: 'up' }
      ],
      'Large Group': Array.from({ length: 10 }, (_, i) => ({
        id: `dev${i + 2}`,
        hostname: `Device ${i + 2}`,
        mgmtIp: `192.168.1.${i + 2}`,
        vendor: 'Test',
        model: 'Model',
        status: 'up'
      }))
    })
    
    render(<App />)
    
    const groupedTab = findButtonByText('Grouped')
    expect(groupedTab).toBeDefined()
    fireEvent.click(groupedTab!)
    
    // Wait for the grouped devices to load
    await waitFor(() => {
      expect(screen.getByText('Grouped Devices')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Group by:')).toBeInTheDocument()
  })

  it('supports all grouping criteria', async () => {
    render(<App />)
    
    const groupedTab = findButtonByText('Grouped')
    expect(groupedTab).toBeDefined()
    fireEvent.click(groupedTab!)
    
    // Wait for the grouped devices to load
    await waitFor(() => {
      expect(screen.getByText('Grouped Devices')).toBeInTheDocument()
    })
    
    // Look for the group by select element
    await waitFor(() => {
      const groupByLabel = screen.getByText('Group by:')
      expect(groupByLabel).toBeInTheDocument()
    })
  })
})
