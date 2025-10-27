import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { WebSocketService } from '../src/websocket'

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3
  
  readyState = MockWebSocket.CONNECTING
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  
  constructor(public url: string) {
    // Simulate connection after a short delay
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 10)
  }
  
  send(data: string) {
    // Mock send implementation
  }
  
  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code: code || 1000, reason: reason || '' }))
    }
  }
}

// Replace global WebSocket with mock
vi.stubGlobal('WebSocket', MockWebSocket)

describe('WebSocketService', () => {
  let wsService: WebSocketService
  
  beforeEach(() => {
    wsService = new WebSocketService('ws://localhost:8000')
  })
  
  afterEach(() => {
    wsService.disconnect()
  })
  
  it('should connect to WebSocket server', async () => {
    await wsService.connect()
    expect(wsService.isConnected()).toBe(true)
  })
  
  it('should handle connection status changes', async () => {
    const connectionHandler = vi.fn()
    wsService.onConnectionChange(connectionHandler)
    
    await wsService.connect()
    
    expect(connectionHandler).toHaveBeenCalledWith(true)
  })
  
  it('should subscribe to message types', async () => {
    await wsService.connect()
    
    const messageHandler = vi.fn()
    wsService.subscribe('test_message', messageHandler)
    
    // Simulate receiving a message
    const mockMessage = { type: 'test_message', data: { test: 'data' } }
    // This would normally be called by the WebSocket onmessage handler
    // For testing, we'll call it directly
    wsService['handleMessage'](mockMessage)
    
    expect(messageHandler).toHaveBeenCalledWith({ test: 'data' })
  })
  
  it('should send messages when connected', async () => {
    await wsService.connect()
    
    const sendSpy = vi.spyOn(wsService['ws']!, 'send')
    
    wsService.send({ type: 'ping' })
    
    expect(sendSpy).toHaveBeenCalledWith('{"type":"ping"}')
  })
  
  it('should not send messages when disconnected', () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    
    wsService.send({ type: 'ping' })
    
    expect(consoleSpy).toHaveBeenCalledWith('WebSocket not connected, cannot send message:', { type: 'ping' })
  })
  
  it('should disconnect properly', async () => {
    await wsService.connect()
    expect(wsService.isConnected()).toBe(true)
    
    wsService.disconnect()
    expect(wsService.isConnected()).toBe(false)
  })
})
