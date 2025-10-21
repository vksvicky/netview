import React, { useEffect, useRef, useState } from 'react'
import { fetchTopology, fetchDevice, fetchInterfaces, fetchInterfaceMetrics, triggerDiscovery, getNetworkStatus } from './api'

console.log('App component loading...')

export const App: React.FC = () => {
  console.log('App component rendering...')
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [network, setNetwork] = useState<any>(null)
  const [topologyData, setTopologyData] = useState<any>({ nodes: [], edges: [] })
  const [debugInfo, setDebugInfo] = useState('App loaded')

  useEffect(() => {
    const loadVisNetwork = async () => {
      try {
        const { DataSet, Network } = await import('vis-network/standalone')
        if (!containerRef.current) return
        
        const nodes = new DataSet([])
        const edges = new DataSet([])
        const net = new Network(containerRef.current, { nodes, edges }, {
          physics: { 
            enabled: false
          },
          interaction: { 
            hover: true,
            selectConnectedEdges: false
          },
          nodes: {
            shape: 'box',
            margin: 10,
            font: { size: 14 },
            borderWidth: 2,
            shadow: true
          },
          edges: {
            width: 2,
            color: { color: '#848484' },
            smooth: { type: 'continuous' }
          }
        })
        setNetwork(net)
        
        net.on('selectNode', async (params: any) => {
          const nodeId = params.nodes?.[0]
          if (!nodeId) return
          const dev = await fetchDevice(nodeId)
          const ifs = await fetchInterfaces(nodeId)
          setSidebar({ device: dev, interfaces: ifs })
        })
        
        return () => { net.destroy() }
      } catch (error) {
        console.error('Failed to load vis-network:', error)
      }
    }
    
    loadVisNetwork()
  }, [])

  useEffect(() => {
    const load = async () => {
      try {
        setDebugInfo('Loading topology...')
        setConnectionStatus('connecting')
        
        // Check network status first
        await checkNetworkStatus()
        
        const data = await fetchTopology()
        console.log('Topology data received:', data)
        setTopologyData(data)
        setConnectionStatus('connected')
        setDebugInfo(`Loaded ${data.nodes.length} nodes, ${data.edges.length} edges`)
        
        if (!network) return
        
        const { DataSet } = await import('vis-network/standalone')
        const nodes = new DataSet(data.nodes || [])
        const edges = new DataSet(data.edges || [])
        network.setData({ nodes, edges })
        
        // Auto-select the first device (router) if available
        if (data.nodes && data.nodes.length > 0) {
          const firstDevice = data.nodes[0]
          // Only auto-select if it's likely a router (ends with .1 or has router vendor)
          if (firstDevice.title.endsWith('.1') || firstDevice.group.toLowerCase().includes('router')) {
            setSidebar({ 
              device: { 
                id: firstDevice.id, 
                hostname: firstDevice.label, 
                mgmtIp: firstDevice.title, 
                vendor: firstDevice.group 
              }, 
              interfaces: [
                { id: `${firstDevice.id}:1`, ifIndex: 1, name: 'Gi0/1', adminStatus: 'up', operStatus: 'up' },
                { id: `${firstDevice.id}:2`, ifIndex: 2, name: 'Gi0/2', adminStatus: 'up', operStatus: 'up' }
              ],
              selectedIf: null, 
              metrics: null 
            })
          }
        }
        
        // Fit the network to show all nodes
        setTimeout(() => {
          network.fit()
        }, 100)
      } catch (error) {
        console.error('Failed to load topology:', error)
        setConnectionStatus('error')
        setDebugInfo(`Error: ${error}`)
      }
    }
    load()
  }, [network])

  // Add periodic network status checking
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        await checkNetworkStatus()
      } catch (error) {
        console.error('Error in periodic network check:', error)
      }
    }, 5000) // Check every 5 seconds for faster detection

    return () => clearInterval(interval)
  }, []) // Empty dependency array to avoid infinite loops

  const [query, setQuery] = useState('')
  const [sidebar, setSidebar] = useState<any>({ device: null, interfaces: [], selectedIf: null, metrics: null })
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting')
  const [networkStatus, setNetworkStatus] = useState<any>({ connected: true, error: null })
  const [showNetworkAlert, setShowNetworkAlert] = useState(false)

  const onSearch = () => {
    if (!network) return
    const allNodes = (network as any).body?.data?.nodes?.get()
    const target = allNodes?.find((n: any) => (n.label || '').toLowerCase().includes(query.toLowerCase()))
    if (target) {
      ;(network as any).focus(target.id, { scale: 1.1 })
      ;(network as any).selectNodes([target.id])
    }
  }

  const onSelectInterface = async (ifc: any) => {
    if (!sidebar.device) return
    const m = await fetchInterfaceMetrics(sidebar.device.id || sidebar.device.deviceId || sidebar.device.hostname, ifc.ifIndex)
    setSidebar((s: any) => ({ ...s, selectedIf: ifc, metrics: m.lastCounters || {} }))
  }

  const checkNetworkStatus = async () => {
    try {
      const status = await getNetworkStatus()
      const wasConnected = networkStatus.connected
      const isNowConnected = status.connected
      
      setNetworkStatus(status)
      
      if (!status.connected) {
        setShowNetworkAlert(true)
        console.warn('Network connectivity issue detected:', status.error)
      } else {
        setShowNetworkAlert(false)
        
        // If network was disconnected and is now connected, trigger discovery
        if (!wasConnected && isNowConnected) {
          console.log('Network reconnected, triggering discovery...')
          // Use setTimeout to avoid state update conflicts
          setTimeout(() => {
            onDiscoverNow()
          }, 1000)
        }
      }
    } catch (error) {
      console.error('Failed to check network status:', error)
      setNetworkStatus({ connected: false, error: 'Unable to check network status' })
      setShowNetworkAlert(true)
    }
  }

  const onDiscoverNow = async () => {
    try {
      // Check network status before discovery
      await checkNetworkStatus()
      
      if (!networkStatus.connected) {
        setShowNetworkAlert(true)
        return
      }
      
      await triggerDiscovery()
      const data = await fetchTopology()
      setTopologyData(data)
      if (!network) return
      
      const { DataSet } = await import('vis-network/standalone')
      const nodes = new DataSet(data.nodes || [])
      const edges = new DataSet(data.edges || [])
      network.setData({ nodes, edges })
    } catch (error) {
      console.error('Discovery failed:', error)
      // Check network status on error
      await checkNetworkStatus()
    }
  }

  return (
    <div style={{ height: '100vh', width: '100vw', display: 'flex', flexDirection: 'column' }}>
      {/* Network Alert Banner */}
      {showNetworkAlert && (
        <div style={{ 
          background: '#ff4444', 
          color: 'white', 
          padding: '8px 16px', 
          textAlign: 'center',
          fontSize: '14px',
          fontWeight: 'bold'
        }}>
          ⚠️ Network Connectivity Issue: {networkStatus.error || 'Unable to connect to network'}
          <button 
            onClick={() => setShowNetworkAlert(false)}
            style={{ 
              marginLeft: '16px', 
              background: 'rgba(255,255,255,0.2)', 
              border: 'none', 
              color: 'white', 
              padding: '4px 8px',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Dismiss
          </button>
        </div>
      )}
      
      <div style={{ padding: 8, borderBottom: '1px solid #ddd', display: 'flex', gap: 8, alignItems: 'center' }}>
        <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search device..." />
        <button onClick={onSearch}>Search</button>
        <button onClick={onDiscoverNow}>Discover now</button>
        <button onClick={checkNetworkStatus}>Refresh Network Status</button>
        <div style={{ marginLeft: 'auto', fontSize: '12px', display: 'flex', gap: '16px' }}>
          <span style={{ color: connectionStatus === 'connected' ? 'green' : connectionStatus === 'error' ? 'red' : 'orange' }}>
            Backend: {connectionStatus}
          </span>
          <span style={{ color: networkStatus.connected ? 'green' : 'red' }}>
            Network: {networkStatus.connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
      <div style={{ flex: 1, display: 'flex' }}>
        <div style={{ height: '100%', width: '100%', background: '#f9f9f9', position: 'relative' }}>
          <div style={{ position: 'absolute', top: 10, left: 10, background: 'rgba(255,255,255,0.9)', padding: 10, borderRadius: 4, fontSize: '12px', zIndex: 1000 }}>
            <div>Nodes: {topologyData.nodes.length}, Edges: {topologyData.edges.length}</div>
            <div>Status: {connectionStatus}</div>
            <div>Network: {network ? 'Loaded' : 'Loading...'}</div>
            <div style={{ color: networkStatus.connected ? 'green' : 'red' }}>
              Connectivity: {networkStatus.connected ? 'Connected' : 'Disconnected'}
            </div>
          </div>
          
          {/* Vis-network container */}
          <div ref={containerRef} style={{ height: '100%', width: '100%', position: 'absolute', top: 0, left: 0 }} />
          
          {/* Router at the top */}
          {topologyData.nodes.length > 0 && topologyData.nodes[0] && (
            <div style={{ 
              position: 'absolute', 
              top: 60, 
              left: 20, 
              right: 20,
              background: 'rgba(255,255,255,0.98)',
              padding: 16,
              borderRadius: 8,
              border: '2px solid #4CAF50',
              zIndex: 1002,
              boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
            }}>
              <h3 style={{ marginTop: 0, marginBottom: 12, color: '#4CAF50' }}>🌐 Router</h3>
              <div style={{ 
                padding: '12px', 
                border: '1px solid #4CAF50', 
                borderRadius: '6px',
                cursor: 'pointer',
                background: '#f8fff8',
                display: 'flex',
                alignItems: 'center',
                gap: '12px'
              }}
              onClick={() => {
                const router = topologyData.nodes[0]
                setSidebar({ 
                  device: { 
                    id: router.id, 
                    hostname: router.label, 
                    mgmtIp: router.title, 
                    vendor: router.group 
                  }, 
                  interfaces: [
                    { id: `${router.id}:1`, ifIndex: 1, name: 'Gi0/1', adminStatus: 'up', operStatus: 'up' },
                    { id: `${router.id}:2`, ifIndex: 2, name: 'Gi0/2', adminStatus: 'up', operStatus: 'up' }
                  ],
                  selectedIf: null, 
                  metrics: null 
                })
              }}
              >
                <div style={{ fontSize: '24px' }}>🌐</div>
                <div>
                  <div style={{ fontWeight: 'bold', fontSize: '16px' }}>{topologyData.nodes[0].label}</div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    IP: {topologyData.nodes[0].title} | Vendor: {topologyData.nodes[0].group}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Other devices */}
          {topologyData.nodes.length > 1 && (
            <div style={{ 
              position: 'absolute', 
              top: 180, 
              left: 20, 
              right: 20,
              bottom: 20,
              background: 'rgba(255,255,255,0.98)',
              padding: 20,
              borderRadius: 8,
              border: '2px solid #ddd',
              zIndex: 1001,
              overflow: 'auto'
            }}>
              <h3 style={{ marginTop: 0, marginBottom: 16 }}>Network Devices ({topologyData.nodes.length - 1})</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '12px' }}>
                {topologyData.nodes.slice(1).map((node: any, index: number) => (
                  <div 
                    key={node.id}
                    style={{ 
                      padding: '12px', 
                      border: '1px solid #ccc', 
                      borderRadius: '6px',
                      cursor: 'pointer',
                      background: '#fff',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                      transition: 'box-shadow 0.2s'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)'}
                    onMouseLeave={(e) => e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)'}
                    onClick={() => {
                      setSidebar({ 
                        device: { 
                          id: node.id, 
                          hostname: node.label, 
                          mgmtIp: node.title, 
                          vendor: node.group 
                        }, 
                        interfaces: [
                          { id: `${node.id}:1`, ifIndex: 1, name: 'Gi0/1', adminStatus: 'up', operStatus: 'up' },
                          { id: `${node.id}:2`, ifIndex: 2, name: 'Gi0/2', adminStatus: 'up', operStatus: 'up' }
                        ],
                        selectedIf: null, 
                        metrics: null 
                      })
                    }}
                  >
                    <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>{node.label}</div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      <div>IP: {node.title}</div>
                      <div>Vendor: {node.group}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {topologyData.nodes.length === 0 && (
            <div style={{ 
              position: 'absolute', 
              top: '50%', 
              left: '50%', 
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              background: 'rgba(255,255,255,0.9)',
              padding: 20,
              borderRadius: 8
            }}>
              <h3>No devices discovered</h3>
              <p>Click "Discover now" to find network devices</p>
            </div>
          )}
        </div>
        <div style={{ width: 320, borderLeft: '1px solid #ddd', padding: 8 }}>
          {sidebar.device ? (
            <div>
              <h3 style={{ marginTop: 0 }}>{sidebar.device.hostname || sidebar.device.id}</h3>
              <div>IP: {sidebar.device.mgmtIp}</div>
              <div>Vendor: {sidebar.device.vendor}</div>
              <h4>Interfaces</h4>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {sidebar.interfaces.map((i: any) => (
                  <li key={i.id} style={{ marginBottom: 6, cursor: 'pointer' }} onClick={() => onSelectInterface(i)}>
                    <div style={{ fontWeight: 600 }}>{i.name} (#{i.ifIndex})</div>
                    <small>Admin: {i.adminStatus} / Oper: {i.operStatus}</small>
                  </li>
                ))}
              </ul>
              {sidebar.selectedIf ? (
                <div style={{ marginTop: 12 }}>
                  <h4>Interface metrics</h4>
                  <pre style={{ background: '#f7f7f7', padding: 8, borderRadius: 4 }}>
{JSON.stringify(sidebar.metrics || {}, null, 2)}
                  </pre>
                </div>
              ) : null}
            </div>
          ) : (
            <div style={{ color: '#666' }}>Select a device</div>
          )}
        </div>
      </div>
    </div>
  )
}


