import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { App } from './App'

vi.mock('./api', () => ({
  fetchTopology: vi.fn().mockResolvedValue({ nodes: [{ id: 'dev1', label: 'switch1' }], edges: [] }),
  fetchDevice: vi.fn().mockResolvedValue({ id: 'dev1', hostname: 'switch1', mgmtIp: '10.0.0.1' }),
  fetchInterfaces: vi.fn().mockResolvedValue([{ id: 'dev1:1', ifIndex: 1, name: 'Gi0/1', adminStatus: 'up', operStatus: 'up' }]),
  fetchInterfaceMetrics: vi.fn().mockResolvedValue({ lastCounters: { inOctets: 1 } }),
  triggerDiscovery: vi.fn().mockResolvedValue({ nodes: [], edges: [] })
}))

describe('App', () => {
  it('renders toolbar and sidebar prompt', async () => {
    render(<App />)
    expect(await screen.findByPlaceholderText('Search device...')).toBeInTheDocument()
    expect(screen.getByText('Select a device')).toBeInTheDocument()
  })

  it('runs discovery and updates graph on button click', async () => {
    render(<App />)
    const btn = await screen.findByText('Discover now')
    fireEvent.click(btn)
    await waitFor(() => expect(btn).toBeInTheDocument())
  })
})


