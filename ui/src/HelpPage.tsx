import React, { useState } from 'react'

interface HelpPageProps {
  onClose: () => void
}

const HelpPage: React.FC<HelpPageProps> = ({ onClose }) => {
  const [activeSection, setActiveSection] = useState<string>('overview')

  const sections = [
    { id: 'overview', title: 'Overview', icon: '📋' },
    { id: 'notifications', title: 'Notifications', icon: '🔔' },
    { id: 'devices', title: 'Devices', icon: '🖥️' },
    { id: 'topology', title: 'Network Topology', icon: '🌐' },
    { id: 'troubleshooting', title: 'Troubleshooting', icon: '🔧' },
    { id: 'glossary', title: 'Glossary', icon: '📚' }
  ]

  const renderOverview = () => (
    <div>
      <h2>📋 NetView Overview</h2>
      <p>NetView is a comprehensive network monitoring tool inspired by NetAlertX that provides real-time visibility into your local network infrastructure.</p>
      
      <h3>Key Features:</h3>
      <ul>
        <li><strong>Device Discovery:</strong> Automatically detect and monitor network devices</li>
        <li><strong>Real-time Monitoring:</strong> Track device status, connectivity, and performance</li>
        <li><strong>Network Topology:</strong> Visualize network structure and connections</li>
        <li><strong>Device History:</strong> Track device events and status changes over time</li>
        <li><strong>Device Grouping:</strong> Organize devices by vendor, type, status, or custom criteria</li>
        <li><strong>Notifications:</strong> Get alerts for network events and device changes</li>
        <li><strong>Performance Metrics:</strong> Monitor interface statistics and network health</li>
      </ul>

      <h3>Getting Started:</h3>
      <ol>
        <li>Click <strong>"Discover now"</strong> to scan your network</li>
        <li>Select devices from the topology view to view details</li>
        <li>Use the <strong>History</strong> tab to track device events</li>
        <li>Use the <strong>Grouped Devices</strong> tab to organize your network</li>
        <li>Monitor notifications for important network events</li>
      </ol>
    </div>
  )

  const renderNotifications = () => (
    <div>
      <h2>🔔 Notifications System</h2>
      
      <h3>Notification Types:</h3>
      <ul>
        <li><strong>New Device:</strong> When a new device joins the network</li>
        <li><strong>Device Offline:</strong> When a device goes offline</li>
        <li><strong>Device Online:</strong> When a device comes back online</li>
        <li><strong>IP Change:</strong> When a device's IP address changes</li>
        <li><strong>Unknown Device:</strong> When an unidentified device is detected</li>
        <li><strong>Security Alert:</strong> When suspicious network activity is detected</li>
        <li><strong>Topology Change:</strong> When network structure changes</li>
      </ul>

      <h3>Notification Actions:</h3>
      <div style={{ marginBottom: '20px' }}>
        <h4>📖 Mark as Read</h4>
        <p><strong>Purpose:</strong> Indicates you have <em>seen</em> the notification</p>
        <p><strong>Effect:</strong> Changes visual styling (removes bold text, changes background)</p>
        <p><strong>When to use:</strong> After reviewing the notification content</p>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h4>✅ Acknowledge (Ack)</h4>
        <p><strong>Purpose:</strong> Indicates you have <em>processed</em> and <em>acted upon</em> the notification</p>
        <p><strong>Effect:</strong> Removes action buttons, marks as acknowledged</p>
        <p><strong>When to use:</strong> After taking action or confirming the issue is handled</p>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h4>🗑️ Delete</h4>
        <p><strong>Purpose:</strong> Permanently removes the notification</p>
        <p><strong>Effect:</strong> Notification is deleted from the system</p>
        <p><strong>When to use:</strong> When the notification is no longer relevant</p>
      </div>

      <h3>Notification Workflow:</h3>
      <ol>
        <li><strong>New notification</strong> → Unread, unacknowledged (bold styling)</li>
        <li><strong>User reads it</strong> → Mark as Read (normal styling)</li>
        <li><strong>User takes action</strong> → Acknowledge (processed)</li>
        <li><strong>User wants to remove</strong> → Delete (permanently removed)</li>
      </ol>

      <h3>Notification Panel Controls:</h3>
      <ul>
        <li><strong>Test:</strong> Create a test notification for demonstration</li>
        <li><strong>Mark All Read:</strong> Mark all notifications as read at once</li>
        <li><strong>Clear All:</strong> Delete all notifications permanently</li>
        <li><strong>✕:</strong> Close the notification panel</li>
      </ul>
    </div>
  )

  const renderDevices = () => (
    <div>
      <h2>🖥️ Device Management</h2>
      
      <h3>Device Information:</h3>
      <ul>
        <li><strong>Hostname:</strong> Device name or identifier</li>
        <li><strong>IP Address:</strong> Management IP address</li>
        <li><strong>MAC Address:</strong> Physical network address</li>
        <li><strong>Vendor:</strong> Device manufacturer</li>
        <li><strong>Model:</strong> Device model number</li>
        <li><strong>Status:</strong> Online/Offline status</li>
        <li><strong>Connection Type:</strong> How the device connects (wired/wireless)</li>
        <li><strong>Roles:</strong> Device functions (router, switch, access point, etc.)</li>
      </ul>

      <h3>Device Status Indicators:</h3>
      <ul>
        <li><strong>🟢 Green:</strong> Device is online and responding</li>
        <li><strong>🔴 Red:</strong> Device is offline or unreachable</li>
        <li><strong>🟡 Yellow:</strong> Device status is unknown or intermittent</li>
      </ul>

      <h3>Device Actions:</h3>
      <ul>
        <li><strong>Select Device:</strong> Click on device in topology to view details</li>
        <li><strong>View Interfaces:</strong> See network interfaces and their status</li>
        <li><strong>View Metrics:</strong> Monitor performance statistics</li>
        <li><strong>View History:</strong> Track device events over time</li>
      </ul>
    </div>
  )

  const renderTopology = () => (
    <div>
      <h2>🌐 Network Topology</h2>
      
      <h3>Topology View:</h3>
      <p>The topology view shows a visual representation of your network structure, including devices and their connections.</p>

      <h3>Navigation:</h3>
      <ul>
        <li><strong>Zoom:</strong> Use mouse wheel or zoom controls</li>
        <li><strong>Pan:</strong> Click and drag to move around</li>
        <li><strong>Select:</strong> Click on devices to view details</li>
        <li><strong>Hover:</strong> Hover over devices for quick information</li>
      </ul>

      <h3>Device Symbols:</h3>
      <ul>
        <li><strong>Router:</strong> Network routing device</li>
        <li><strong>Switch:</strong> Network switching device</li>
        <li><strong>Access Point:</strong> Wireless access point</li>
        <li><strong>Computer:</strong> End-user device</li>
        <li><strong>Unknown:</strong> Unidentified device</li>
      </ul>

      <h3>Connection Lines:</h3>
      <ul>
        <li><strong>Solid Lines:</strong> Direct network connections</li>
        <li><strong>Dashed Lines:</strong> Logical or wireless connections</li>
        <li><strong>Thick Lines:</strong> High-bandwidth connections</li>
        <li><strong>Thin Lines:</strong> Standard connections</li>
      </ul>
    </div>
  )

  const renderTroubleshooting = () => (
    <div>
      <h2>🔧 Troubleshooting Guide</h2>
      
      <h3>Common Issues:</h3>
      
      <div style={{ marginBottom: '20px' }}>
        <h4>❌ No devices discovered</h4>
        <p><strong>Possible causes:</strong></p>
        <ul>
          <li>SNMP not enabled on devices</li>
          <li>Wrong SNMP community string</li>
          <li>Firewall blocking SNMP traffic</li>
          <li>Network connectivity issues</li>
        </ul>
        <p><strong>Solutions:</strong></p>
        <ul>
          <li>Enable SNMP on network devices</li>
          <li>Check SNMP community string configuration</li>
          <li>Verify firewall rules allow SNMP (UDP port 161)</li>
          <li>Test network connectivity with ping</li>
        </ul>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h4>⚠️ Devices showing as offline</h4>
        <p><strong>Possible causes:</strong></p>
        <ul>
          <li>Device is actually offline</li>
          <li>SNMP service stopped</li>
          <li>Network connectivity issues</li>
          <li>SNMP configuration changed</li>
        </ul>
        <p><strong>Solutions:</strong></p>
        <ul>
          <li>Check device power and network cables</li>
          <li>Restart SNMP service on device</li>
          <li>Test connectivity with ping/telnet</li>
          <li>Verify SNMP configuration</li>
        </ul>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h4>🔄 Frequent topology changes</h4>
        <p><strong>Possible causes:</strong></p>
        <ul>
          <li>Network instability</li>
          <li>Devices rebooting frequently</li>
          <li>SNMP timeout issues</li>
          <li>Discovery interval too frequent</li>
        </ul>
        <p><strong>Solutions:</strong></p>
        <ul>
          <li>Check network stability</li>
          <li>Investigate device reboot causes</li>
          <li>Adjust SNMP timeout settings</li>
          <li>Increase discovery interval</li>
        </ul>
      </div>

      <h3>Performance Issues:</h3>
      
      <div style={{ marginBottom: '20px' }}>
        <h4>🐌 Slow discovery</h4>
        <p><strong>Solutions:</strong></p>
        <ul>
          <li>Reduce discovery scope (smaller IP ranges)</li>
          <li>Increase SNMP timeout values</li>
          <li>Use faster SNMP community strings</li>
          <li>Check network bandwidth</li>
        </ul>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h4>💾 High memory usage</h4>
        <p><strong>Solutions:</strong></p>
        <ul>
          <li>Clear old device history</li>
          <li>Reduce discovery frequency</li>
          <li>Limit number of monitored devices</li>
          <li>Restart the application</li>
        </ul>
      </div>

      <h3>Debug Information:</h3>
      <p>Enable debug mode to get detailed logging information for troubleshooting:</p>
      <ul>
        <li>Check browser console for JavaScript errors</li>
        <li>Review backend logs for API errors</li>
        <li>Monitor network traffic with browser dev tools</li>
        <li>Test SNMP connectivity with external tools</li>
      </ul>
    </div>
  )

  const renderGlossary = () => (
    <div>
      <h2>📚 Glossary & Acronyms</h2>
      
      <h3>Network Terms:</h3>
      <dl>
        <dt><strong>SNMP (Simple Network Management Protocol)</strong></dt>
        <dd>Protocol used to monitor and manage network devices</dd>
        
        <dt><strong>OID (Object Identifier)</strong></dt>
        <dd>Unique identifier for SNMP objects</dd>
        
        <dt><strong>Community String</strong></dt>
        <dd>Password-like string used for SNMP authentication</dd>
        
        <dt><strong>MIB (Management Information Base)</strong></dt>
        <dd>Database of network management information</dd>
        
        <dt><strong>MAC Address</strong></dt>
        <dd>Media Access Control address - unique hardware identifier</dd>
        
        <dt><strong>IP Address</strong></dt>
        <dd>Internet Protocol address - network identifier</dd>
        
        <dt><strong>Interface</strong></dt>
        <dd>Network port or connection point on a device</dd>
        
        <dt><strong>Topology</strong></dt>
        <dd>Physical or logical structure of a network</dd>
      </dl>

      <h3>Device Types:</h3>
      <dl>
        <dt><strong>Router</strong></dt>
        <dd>Device that forwards data packets between networks</dd>
        
        <dt><strong>Switch</strong></dt>
        <dd>Device that connects devices within a network</dd>
        
        <dt><strong>Access Point (AP)</strong></dt>
        <dd>Device that provides wireless network access</dd>
        
        <dt><strong>Gateway</strong></dt>
        <dd>Device that connects different networks</dd>
        
        <dt><strong>Bridge</strong></dt>
        <dd>Device that connects network segments</dd>
      </dl>

      <h3>Status Terms:</h3>
      <dl>
        <dt><strong>Online/Up</strong></dt>
        <dd>Device is active and responding</dd>
        
        <dt><strong>Offline/Down</strong></dt>
        <dd>Device is inactive or unreachable</dd>
        
        <dt><strong>Unknown</strong></dt>
        <dd>Device status cannot be determined</dd>
        
        <dt><strong>Intermittent</strong></dt>
        <dd>Device status changes frequently</dd>
      </dl>

      <h3>NetView Specific Terms:</h3>
      <dl>
        <dt><strong>Discovery</strong></dt>
        <dd>Process of finding and identifying network devices</dd>
        
        <dt><strong>Device History</strong></dt>
        <dd>Record of device events and status changes</dd>
        
        <dt><strong>Device Grouping</strong></dt>
        <dd>Organizing devices by common characteristics</dd>
        
        <dt><strong>Notification</strong></dt>
        <dd>Alert about network events or device changes</dd>
        
        <dt><strong>Acknowledge (Ack)</strong></dt>
        <dd>Confirm that a notification has been processed</dd>
        
        <dt><strong>Mark as Read</strong></dt>
        <dd>Indicate that a notification has been viewed</dd>
      </dl>

      <h3>Performance Metrics:</h3>
      <dl>
        <dt><strong>Bandwidth</strong></dt>
        <dd>Data transfer capacity of a network connection</dd>
        
        <dt><strong>Latency</strong></dt>
        <dd>Time delay in data transmission</dd>
        
        <dt><strong>Throughput</strong></dt>
        <dd>Actual data transfer rate</dd>
        
        <dt><strong>Packet Loss</strong></dt>
        <dd>Percentage of data packets that don't reach destination</dd>
        
        <dt><strong>Jitter</strong></dt>
        <dd>Variation in packet arrival times</dd>
      </dl>
    </div>
  )

  const renderContent = () => {
    switch (activeSection) {
      case 'overview': return renderOverview()
      case 'notifications': return renderNotifications()
      case 'devices': return renderDevices()
      case 'topology': return renderTopology()
      case 'troubleshooting': return renderTroubleshooting()
      case 'glossary': return renderGlossary()
      default: return renderOverview()
    }
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.5)',
      zIndex: 3000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '8px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
        width: '90%',
        maxWidth: '1000px',
        height: '90%',
        maxHeight: '800px',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px',
          borderBottom: '1px solid #eee',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h1 style={{ margin: 0, fontSize: '24px' }}>📖 NetView Help</h1>
          <button
            onClick={onClose}
            style={{
              background: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              padding: '8px 16px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            ✕ Close
          </button>
        </div>

        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* Sidebar */}
          <div style={{
            width: '250px',
            background: '#f8f9fa',
            borderRight: '1px solid #eee',
            padding: '20px 0',
            overflowY: 'auto'
          }}>
            {sections.map(section => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                style={{
                  width: '100%',
                  padding: '12px 20px',
                  border: 'none',
                  background: activeSection === section.id ? '#007bff' : 'transparent',
                  color: activeSection === section.id ? 'white' : '#333',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontSize: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                <span>{section.icon}</span>
                {section.title}
              </button>
            ))}
          </div>

          {/* Content */}
          <div style={{
            flex: 1,
            padding: '20px',
            overflowY: 'auto',
            fontSize: '14px',
            lineHeight: '1.6'
          }}>
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  )
}

export default HelpPage
