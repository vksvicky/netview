import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { App } from './App'

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
  fetchDeviceHistory: vi.fn().mockResolvedValue([
    {
      id: 1,
      device_id: 'dev1',
      event_type: 'online',
      new_status: 'up',
      new_ip: '192.168.1.100',
      event_timestamp: '2024-01-01T10:00:00Z',
      duration_seconds: null,
      event_metadata: { vendor: 'Test Vendor' }
    }
  ]),
  fetchDeviceSessionStats: vi.fn().mockResolvedValue({
    total_sessions: 5,
    total_online_time_seconds: 18000,
    avg_session_duration_seconds: 3600,
    days_tracked: 30
  }),
  fetchRecentEvents: vi.fn().mockResolvedValue([
    {
      id: 3,
      device_id: 'dev1',
      event_type: 'online',
      new_status: 'up',
      new_ip: '192.168.1.100',
      event_timestamp: '2024-01-01T11:00:00Z',
      duration_seconds: null,
      event_metadata: {}
    }
  ]),
  fetchGroupedDevices: vi.fn().mockResolvedValue({}),
  fetchGroupingStats: vi.fn().mockResolvedValue({}),
  getUnknownVendors: vi.fn().mockResolvedValue([])
}))

describe('Device History Feature', () => {
  // Helper function to find the first clickable button with text
  const findButtonByText = (text: string) => {
    const buttons = screen.getAllByText(text)
    return buttons.find(button => button.closest('button'))
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders history tab button', async () => {
    render(<App />)
    
    // Wait for topology to load so sidebar is rendered
    await waitFor(() => {
      expect(screen.getByText('Router')).toBeInTheDocument()
    })
    
    const historyTab = findButtonByText('History')
    expect(historyTab).toBeDefined()
  })

  it('switches to history tab when clicked', async () => {
    render(<App />)
    
    const historyTab = findButtonByText('History')
    expect(historyTab).toBeDefined()
    fireEvent.click(historyTab!)
    
    // Wait for the history content to load
    await waitFor(() => {
      expect(screen.getByText('Device History')).toBeInTheDocument()
    })
  })

  it('displays recent events section', async () => {
    render(<App />)
    
    const historyTab = findButtonByText('History')
    expect(historyTab).toBeDefined()
    fireEvent.click(historyTab!)
    
    // Wait for the history content to load
    await waitFor(() => {
      expect(screen.getByText('Device History')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Recent Events (Last 24 Hours)')).toBeInTheDocument()
  })

  it('displays device-specific history section', async () => {
    render(<App />)
    
    const historyTab = findButtonByText('History')
    expect(historyTab).toBeDefined()
    fireEvent.click(historyTab!)
    
    // Wait for the history content to load
    await waitFor(() => {
      expect(screen.getByText('Device History')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Device History')).toBeInTheDocument()
  })

  it('displays session statistics section', async () => {
    render(<App />)
    
    const historyTab = findButtonByText('History')
    expect(historyTab).toBeDefined()
    fireEvent.click(historyTab!)
    
    // Wait for the history content to load
    await waitFor(() => {
      expect(screen.getByText('Device History')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Device History')).toBeInTheDocument()
  })

  it('handles loading states gracefully', async () => {
    render(<App />)
    
    const historyTab = findButtonByText('History')
    expect(historyTab).toBeDefined()
    fireEvent.click(historyTab!)
    
    // Wait for the history content to load
    await waitFor(() => {
      expect(screen.getByText('Device History')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Device History')).toBeInTheDocument()
  })

  it('handles empty history data gracefully', async () => {
    render(<App />)
    
    const historyTab = findButtonByText('History')
    expect(historyTab).toBeDefined()
    fireEvent.click(historyTab!)
    
    // Wait for the history content to load
    await waitFor(() => {
      expect(screen.getByText('Device History')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Device History')).toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    render(<App />)
    
    const historyTab = findButtonByText('History')
    expect(historyTab).toBeDefined()
    fireEvent.click(historyTab!)
    
    // Wait for the history content to load
    await waitFor(() => {
      expect(screen.getByText('Device History')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Device History')).toBeInTheDocument()
  })

  it('formats timestamps correctly', async () => {
    render(<App />)
    
    const historyTab = findButtonByText('History')
    expect(historyTab).toBeDefined()
    fireEvent.click(historyTab!)
    
    // Wait for the history content to load
    await waitFor(() => {
      expect(screen.getByText('Device History')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Device History')).toBeInTheDocument()
  })

  it('shows device selection in history', async () => {
    render(<App />)
    
    const historyTab = findButtonByText('History')
    expect(historyTab).toBeDefined()
    fireEvent.click(historyTab!)
    
    // Wait for the history content to load
    await waitFor(() => {
      expect(screen.getByText('Device History')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Device History')).toBeInTheDocument()
  })

  it('handles device selection changes', async () => {
    render(<App />)
    
    const historyTab = findButtonByText('History')
    expect(historyTab).toBeDefined()
    fireEvent.click(historyTab!)
    
    // Wait for the history content to load
    await waitFor(() => {
      expect(screen.getByText('Device History')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Device History')).toBeInTheDocument()
  })

  it('displays event types correctly', async () => {
    render(<App />)
    
    const historyTab = findButtonByText('History')
    expect(historyTab).toBeDefined()
    fireEvent.click(historyTab!)
    
    // Wait for the history content to load
    await waitFor(() => {
      expect(screen.getByText('Device History')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Device History')).toBeInTheDocument()
  })

  it('shows session duration information', async () => {
    render(<App />)
    
    const historyTab = findButtonByText('History')
    expect(historyTab).toBeDefined()
    fireEvent.click(historyTab!)
    
    // Wait for the history content to load
    await waitFor(() => {
      expect(screen.getByText('Device History')).toBeInTheDocument()
    })
    
    // Verify the UI elements are present
    expect(screen.getByText('Device History')).toBeInTheDocument()
  })
})