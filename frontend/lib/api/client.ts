import { ApiResponse, PaginatedResponse } from '../types';

// API Client Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';
const API_TIMEOUT = 30000; // 30 seconds

// Custom error class for API errors
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Request configuration interface
interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  withAuth?: boolean;
  retries?: number;
  cache?: boolean;
}

// Token management
class TokenManager {
  private static instance: TokenManager;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private tokenExpiresAt: Date | null = null;
  private refreshPromise: Promise<string | null> | null = null;

  static getInstance(): TokenManager {
    if (!TokenManager.instance) {
      TokenManager.instance = new TokenManager();
    }
    return TokenManager.instance;
  }

  setTokens(accessToken: string, refreshToken: string, expiresAt: string): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    this.tokenExpiresAt = new Date(expiresAt);
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  isTokenExpired(): boolean {
    if (!this.tokenExpiresAt) return true;
    return new Date() >= this.tokenExpiresAt;
  }

  async getValidToken(): Promise<string | null> {
    if (!this.accessToken) return null;

    if (!this.isTokenExpired()) {
      return this.accessToken;
    }

    // If already refreshing, wait for that promise
    if (this.refreshPromise) {
      return await this.refreshPromise;
    }

    // Start refresh process
    this.refreshPromise = this.refreshTokens();
    const newToken = await this.refreshPromise;
    this.refreshPromise = null;

    return newToken;
  }

  private async refreshTokens(): Promise<string | null> {
    if (!this.refreshToken) return null;

    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refreshToken: this.refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      this.setTokens(data.accessToken, data.refreshToken, data.expiresAt);
      return data.accessToken;
    } catch (error) {
      // Clear tokens on refresh failure
      this.clearTokens();
      return null;
    }
  }

  clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    this.tokenExpiresAt = null;
    this.refreshPromise = null;
  }
}

// HTTP Client class
class HttpClient {
  private tokenManager = TokenManager.getInstance();
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();

  async request<T>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const {
      method = 'GET',
      headers = {},
      body,
      timeout = API_TIMEOUT,
      withAuth = true,
      retries = 3,
      cache = false,
    } = config;

    // Check cache for GET requests
    if (method === 'GET' && cache) {
      const cacheKey = this.getCacheKey(endpoint, config);
      const cached = this.cache.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < cached.ttl) {
        return cached.data;
      }
    }

    // Prepare headers
    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    };

    // Add authentication header
    if (withAuth) {
      const token = await this.tokenManager.getValidToken();
      if (token) {
        requestHeaders.Authorization = `Bearer ${token}`;
      }
    }

    // Prepare request configuration
    const requestConfig: RequestInit = {
      method,
      headers: requestHeaders,
      body: body ? JSON.stringify(body) : undefined,
    };

    // Add timeout using AbortController
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    requestConfig.signal = controller.signal;

    let lastError: Error;

    // Retry logic
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, requestConfig);
        clearTimeout(timeoutId);

        // Handle different response statuses
        if (response.ok) {
          const data = await response.json();

          // Cache successful GET requests
          if (method === 'GET' && cache) {
            const cacheKey = this.getCacheKey(endpoint, config);
            this.cache.set(cacheKey, {
              data,
              timestamp: Date.now(),
              ttl: 5 * 60 * 1000, // 5 minutes default TTL
            });
          }

          return data;
        }

        // Handle authentication errors
        if (response.status === 401) {
          this.tokenManager.clearTokens();
          throw new ApiError('Authentication required', 401, 'UNAUTHORIZED');
        }

        // Handle other HTTP errors
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          errorData.message || `HTTP ${response.status}`,
          response.status,
          errorData.code,
          errorData.details
        );
      } catch (error) {
        lastError = error as Error;

        // Don't retry on certain errors
        if (
          error instanceof ApiError ||
          error instanceof TypeError ||
          attempt === retries
        ) {
          throw error;
        }

        // Exponential backoff for retries
        const delay = Math.pow(2, attempt) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    throw lastError!;
  }

  // Helper methods for common HTTP methods
  async get<T>(endpoint: string, config?: Omit<RequestConfig, 'method'>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'GET' });
  }

  async post<T>(endpoint: string, body?: any, config?: Omit<RequestConfig, 'method' | 'body'>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'POST', body });
  }

  async put<T>(endpoint: string, body?: any, config?: Omit<RequestConfig, 'method' | 'body'>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'PUT', body });
  }

  async patch<T>(endpoint: string, body?: any, config?: Omit<RequestConfig, 'method' | 'body'>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'PATCH', body });
  }

  async delete<T>(endpoint: string, config?: Omit<RequestConfig, 'method'>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' });
  }

  // Paginated request helper
  async getPaginated<T>(
    endpoint: string,
    params?: Record<string, any>,
    config?: Omit<RequestConfig, 'method'>
  ): Promise<PaginatedResponse<T>> {
    const queryString = params ? '?' + new URLSearchParams(params).toString() : '';
    return this.request<T[]>(`${endpoint}${queryString}`, { ...config, method: 'GET' }) as Promise<PaginatedResponse<T>>;
  }

  // Upload file helper
  async uploadFile<T>(
    endpoint: string,
    file: File,
    config?: Omit<RequestConfig, 'method' | 'body' | 'headers'>
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      headers: {}, // Let browser set Content-Type for FormData
      body: formData,
    });
  }

  // Cache management
  clearCache(pattern?: RegExp): void {
    if (pattern) {
      for (const [key] of this.cache.entries()) {
        if (pattern.test(key)) {
          this.cache.delete(key);
        }
      }
    } else {
      this.cache.clear();
    }
  }

  private getCacheKey(endpoint: string, config: RequestConfig): string {
    return `${endpoint}-${JSON.stringify(config)}`;
  }

  // Set authentication tokens
  setAuthTokens(accessToken: string, refreshToken: string, expiresAt: string): void {
    this.tokenManager.setTokens(accessToken, refreshToken, expiresAt);
  }

  // Clear authentication tokens
  clearAuthTokens(): void {
    this.tokenManager.clearTokens();
    this.clearCache(); // Clear cache when logging out
  }
}

// Create and export singleton instance
export const apiClient = new HttpClient();

// Export token manager for use in stores
export const tokenManager = TokenManager.getInstance();

// Request interceptor for global error handling
export const setupGlobalErrorHandling = (onError?: (error: ApiError) => void) => {
  const originalRequest = apiClient.request.bind(apiClient);

  apiClient.request = async function<T>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    try {
      return await originalRequest(endpoint, config);
    } catch (error) {
      if (error instanceof ApiError && onError) {
        onError(error);
      }
      throw error;
    }
  };
};

// WebSocket client for real-time features
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners = new Map<string, Set<(data: any) => void>>();
  private connectionState: 'connecting' | 'connected' | 'disconnected' | 'error' = 'disconnected';

  constructor(url: string) {
    this.url = url;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.connectionState = 'connecting';
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.connectionState = 'connected';
        this.reconnectAttempts = 0;

        // Send authentication token if available
        const token = tokenManager.getAccessToken();
        if (token) {
          this.send({ type: 'auth', token });
        }

        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };

      this.ws.onclose = () => {
        this.connectionState = 'disconnected';
        this.handleReconnect();
      };

      this.ws.onerror = (error) => {
        this.connectionState = 'error';
        console.error('WebSocket error:', error);
        reject(error);
      };
    });
  }

  private handleMessage(message: any): void {
    const { type, payload } = message;
    const typeListeners = this.listeners.get(type);

    if (typeListeners) {
      typeListeners.forEach(listener => listener(payload));
    }

    // Emit to global listeners
    const globalListeners = this.listeners.get('*');
    if (globalListeners) {
      globalListeners.forEach(listener => listener(message));
    }
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

      setTimeout(() => {
        console.log(`Reconnecting WebSocket... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect().catch(console.error);
      }, delay);
    }
  }

  subscribe(type: string, listener: (data: any) => void): () => void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }

    this.listeners.get(type)!.add(listener);

    return () => {
      const typeListeners = this.listeners.get(type);
      if (typeListeners) {
        typeListeners.delete(listener);
        if (typeListeners.size === 0) {
          this.listeners.delete(type);
        }
      }
    };
  }

  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected. Message not sent:', message);
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connectionState = 'disconnected';
  }

  getConnectionState(): string {
    return this.connectionState;
  }

  isConnected(): boolean {
    return this.connectionState === 'connected';
  }
}

// Create WebSocket client instance
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
export const wsClient = new WebSocketClient(WS_URL);