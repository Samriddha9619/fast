// WebSocket message types
export interface WebSocketMessage {
  type: 'join_room' | 'send_message' | 'typing' | 'new_message' | 'user_typing' | 'error';
  room_id?: number;
  content?: string;
  anonymous_name?: string;
  is_typing?: boolean;
  message?: any;
  error?: string;
}

export interface WebSocketCallbacks {
  onMessage?: (data: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectInterval: number = 3000;
  private callbacks: WebSocketCallbacks = {};
  private isConnecting: boolean = false;
  private reconnectTimer: number | null = null;

  connect(token: string | null = null, isAnonymous: boolean = false): void {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.isConnecting = true;
    
    let url = 'ws://localhost:8001/ws';
    const params = new URLSearchParams();
    
    if (token && !isAnonymous) {
      params.append('token', token);
    } else if (isAnonymous) {
      params.append('anonymous', 'true');
    }
    
    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    try {
      this.ws = new WebSocket(url);
      this.setupEventHandlers();
    } catch (error) {
      this.isConnecting = false;
      this.handleError(error as Event);
    }
  }

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.callbacks.onConnect?.();
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        this.callbacks.onMessage?.(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.ws.onclose = (event: CloseEvent) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      this.isConnecting = false;
      this.callbacks.onDisconnect?.();
      
      if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error: Event) => {
      console.error('WebSocket error:', error);
      this.isConnecting = false;
      this.handleError(error);
    };
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
    
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, this.reconnectInterval);
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.callbacks = {};
  }

  joinRoom(roomId: number, anonymousName?: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message: WebSocketMessage = {
        type: 'join_room',
        room_id: roomId,
        ...(anonymousName && { anonymous_name: anonymousName })
      };
      this.ws.send(JSON.stringify(message));
    }
  }

  sendMessage(roomId: number, content: string, anonymousName?: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message: WebSocketMessage = {
        type: 'send_message',
        room_id: roomId,
        content: content,
        ...(anonymousName && { anonymous_name: anonymousName })
      };
      this.ws.send(JSON.stringify(message));
    }
  }

  sendTyping(roomId: number, isTyping: boolean, anonymousName?: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message: WebSocketMessage = {
        type: 'typing',
        room_id: roomId,
        is_typing: isTyping,
        ...(anonymousName && { anonymous_name: anonymousName })
      };
      this.ws.send(JSON.stringify(message));
    }
  }

  onMessage(callback: (data: WebSocketMessage) => void): void {
    this.callbacks.onMessage = callback;
  }

  onError(callback: (error: Event) => void): void {
    this.callbacks.onError = callback;
  }

  onConnect(callback: () => void): void {
    this.callbacks.onConnect = callback;
  }

  onDisconnect(callback: () => void): void {
    this.callbacks.onDisconnect = callback;
  }

  private handleError(error: Event): void {
    this.callbacks.onError?.(error);
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}

export default new WebSocketService();