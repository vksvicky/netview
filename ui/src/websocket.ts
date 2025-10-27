/**
 * WebSocket service for real-time updates
 */

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: string;
  message?: string;
}

export interface DeviceUpdateMessage extends WebSocketMessage {
  type: 'device_update';
  data: {
    id: string;
    hostname?: string;
    mgmt_ip?: string;
    vendor?: string;
    model?: string;
    status?: string;
    connection_type?: string;
    last_seen?: string;
  };
}

export interface TopologyUpdateMessage extends WebSocketMessage {
  type: 'topology_update';
  data: {
    nodes: Array<{
      id: string;
      label: string;
      title: string;
      group: string;
    }>;
    edges: Array<{
      id: string;
      from: string;
      to: string;
      label?: string;
    }>;
  };
}

export interface NotificationMessage extends WebSocketMessage {
  type: 'notification';
  data: {
    id: number;
    type: string;
    title: string;
    message: string;
    device_id?: string;
    severity: string;
    is_read: boolean;
    is_acknowledged: boolean;
    created_at: string;
    notification_data: any;
  };
}

export interface SystemStatusMessage extends WebSocketMessage {
  type: 'system_status';
  data: {
    status: string;
    message: string;
    timestamp: string;
  };
}

export type AllWebSocketMessages = 
  | DeviceUpdateMessage 
  | TopologyUpdateMessage 
  | NotificationMessage 
  | SystemStatusMessage;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private maxReconnectDelay = 30000; // Max 30 seconds
  private isConnecting = false;
  private messageHandlers: Map<string, Array<(data: any) => void>> = new Map();
  private connectionHandlers: Array<(connected: boolean) => void> = [];
  private pingInterval: NodeJS.Timeout | null = null;
  private pongTimeout: NodeJS.Timeout | null = null;

  constructor(private baseUrl: string = 'ws://localhost:8000') {}

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
        resolve();
        return;
      }

      this.isConnecting = true;
      
      try {
        this.ws = new WebSocket(`${this.baseUrl}/ws`);
        
        this.ws.onopen = () => {
          console.log('🔌 WebSocket connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;
          this.startPingInterval();
          this.notifyConnectionHandlers(true);
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: AllWebSocketMessages = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('🔌 WebSocket disconnected:', event.code, event.reason);
          this.isConnecting = false;
          this.stopPingInterval();
          this.notifyConnectionHandlers(false);
          
          // Attempt to reconnect if not a manual close
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('🔌 WebSocket error:', error);
          this.isConnecting = false;
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    this.stopPingInterval();
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Send a message to the WebSocket server
   */
  send(message: WebSocketMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message:', message);
    }
  }

  /**
   * Subscribe to a specific message type
   */
  subscribe(messageType: string, handler: (data: any) => void): void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)!.push(handler);
  }

  /**
   * Unsubscribe from a specific message type
   */
  unsubscribe(messageType: string, handler: (data: any) => void): void {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Subscribe to connection status changes
   */
  onConnectionChange(handler: (connected: boolean) => void): void {
    this.connectionHandlers.push(handler);
  }

  /**
   * Unsubscribe from connection status changes
   */
  offConnectionChange(handler: (connected: boolean) => void): void {
    const index = this.connectionHandlers.indexOf(handler);
    if (index > -1) {
      this.connectionHandlers.splice(index, 1);
    }
  }

  private handleMessage(message: AllWebSocketMessages): void {
    console.log('📨 WebSocket message received:', message);

    // Handle pong responses
    if (message.type === 'pong') {
      if (this.pongTimeout) {
        clearTimeout(this.pongTimeout);
        this.pongTimeout = null;
      }
      return;
    }

    // Notify handlers for this message type
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message.data);
        } catch (error) {
          console.error('Error in WebSocket message handler:', error);
        }
      });
    }
  }

  private notifyConnectionHandlers(connected: boolean): void {
    this.connectionHandlers.forEach(handler => {
      try {
        handler(connected);
      } catch (error) {
        console.error('Error in connection handler:', error);
      }
    });
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), this.maxReconnectDelay);
    
    console.log(`🔄 Scheduling WebSocket reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      if (this.reconnectAttempts <= this.maxReconnectAttempts) {
        this.connect().catch(error => {
          console.error('Reconnection failed:', error);
        });
      }
    }, delay);
  }

  private startPingInterval(): void {
    this.stopPingInterval();
    this.pingInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'ping' });
        
        // Set timeout for pong response
        this.pongTimeout = setTimeout(() => {
          console.warn('WebSocket pong timeout, connection may be stale');
          if (this.ws) {
            this.ws.close();
          }
        }, 5000); // 5 second timeout
      }
    }, 30000); // Ping every 30 seconds
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    if (this.pongTimeout) {
      clearTimeout(this.pongTimeout);
      this.pongTimeout = null;
    }
  }
}

// Global WebSocket service instance
export const wsService = new WebSocketService();
