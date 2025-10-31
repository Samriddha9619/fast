import axios, { type AxiosResponse, type AxiosError } from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

// Types
export interface User {
  id: number;
  username: string;
  email: string;
}

export interface AuthResponse {
  token: string;
  user_id: number;
  username: string;
}

export interface ChatRoom {
  id: number;
  name: string;
  room_type: 'private' | 'group' | 'anonymous';
  is_active: boolean;
  created_at: string;
  participants?: User[];
  last_message?: Message;
}

export interface Message {
  id: number;
  content: string;
  sender: User;
  room: number;
  timestamp: string;
  anonymous_name?: string;
}

export interface FriendRequest {
  id: number;
  sender: User;
  receiver: User;
  status: 'pending' | 'accepted' | 'rejected';
  created_at: string;
}

export interface Friendship {
  id: number;
  user1: User;
  user2: User;
  created_at: string;
}

export interface UserSearchResult extends User {
  friendship_status: 'none' | 'friend' | 'request_sent' | 'request_received';
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: async (username: string, email: string, password: string): Promise<ApiResponse<{ message: string; user_id: number; username: string }>> => {
    try {
      console.log('Attempting registration with:', { username, email, password: '***' });
      const response = await api.post<{ message: string; user_id: number; username: string }>('/auth/register/', {
        username,
        email,
        password,
      });
      console.log('Registration response:', response.data);
      return { success: true, data: response.data };
    } catch (error) {
      const axiosError = error as AxiosError;
      console.error('Registration error:', axiosError.response?.data || axiosError.message);
      return { 
        success: false, 
        error: (axiosError.response?.data as any)?.error || 'Registration failed' 
      };
    }
  },

  login: async (username: string, password: string): Promise<ApiResponse<AuthResponse>> => {
    try {
      console.log('Attempting login with:', { username, password: '***' });
      console.log('API Base URL:', API_BASE_URL);
      console.log('Full URL:', `${API_BASE_URL}/auth/login/`);
      
      const response = await api.post<AuthResponse>('/auth/login/', {
        username,
        password,
      });
      console.log('Login response:', response.data);
      return { success: true, data: response.data };
    } catch (error) {
      const axiosError = error as AxiosError;
      console.error('Login error details:');
      console.error('- Status:', axiosError.response?.status);
      console.error('- Status Text:', axiosError.response?.statusText);
      console.error('- Response Data:', axiosError.response?.data);
      console.error('- Request URL:', axiosError.config?.url);
      console.error('- Request Method:', axiosError.config?.method);
      console.error('- Full Error:', axiosError.message);
      
      return { 
        success: false, 
        error: (axiosError.response?.data as any)?.error || axiosError.message || 'Login failed' 
      };
    }
  },

  getProfile: async (): Promise<ApiResponse<User>> => {
    try {
      const response = await api.get<User>('/auth/profile/');
      return { success: true, data: response.data };
    } catch (error) {
      const axiosError = error as AxiosError;
      return { 
        success: false, 
        error: (axiosError.response?.data as any)?.message || 'Failed to get profile' 
      };
    }
  },
};

export const userAPI = {
  searchUsers: async (query: string): Promise<ApiResponse<UserSearchResult[]>> => {
    try {
      const response = await api.get<UserSearchResult[]>(`/users/search/?q=${encodeURIComponent(query)}`);
      return { success: true, data: response.data };
    } catch (error) {
      const axiosError = error as AxiosError;
      return { 
        success: false, 
        error: (axiosError.response?.data as any)?.message || 'Search failed' 
      };
    }
  },
};

export const friendAPI = {
  getFriends: async (): Promise<ApiResponse<Friendship[]>> => {
    try {
      const response = await api.get<Friendship[]>('/friends/');
      return { success: true, data: response.data };
    } catch (error) {
      const axiosError = error as AxiosError;
      return { 
        success: false, 
        error: (axiosError.response?.data as any)?.message || 'Failed to get friends' 
      };
    }
  },

  getFriendRequests: async (): Promise<ApiResponse<FriendRequest[]>> => {
    try {
      const response = await api.get<FriendRequest[]>('/friends/requests/');
      return { success: true, data: response.data };
    } catch (error) {
      const axiosError = error as AxiosError;
      return { 
        success: false, 
        error: (axiosError.response?.data as any)?.message || 'Failed to get friend requests' 
      };
    }
  },

  sendFriendRequest: async (receiverId: number): Promise<ApiResponse<FriendRequest>> => {
    try {
      const response = await api.post<FriendRequest>('/friends/request/', { receiver_id: receiverId });
      return { success: true, data: response.data };
    } catch (error) {
      const axiosError = error as AxiosError;
      return { 
        success: false, 
        error: (axiosError.response?.data as any)?.message || 'Failed to send friend request' 
      };
    }
  },

  respondFriendRequest: async (requestId: number, action: 'accept' | 'reject'): Promise<ApiResponse<FriendRequest>> => {
    try {
      const response = await api.post<FriendRequest>(`/friends/request/${requestId}/respond/`, { action });
      return { success: true, data: response.data };
    } catch (error) {
      const axiosError = error as AxiosError;
      return { 
        success: false, 
        error: (axiosError.response?.data as any)?.message || 'Failed to respond to friend request' 
      };
    }
  },
};

export const chatAPI = {
  getChatRooms: async (): Promise<ApiResponse<ChatRoom[]>> => {
    try {
      const response = await api.get<ChatRoom[]>('/chat/rooms/');
      return { success: true, data: response.data };
    } catch (error) {
      const axiosError = error as AxiosError;
      return { 
        success: false, 
        error: (axiosError.response?.data as any)?.message || 'Failed to get chat rooms' 
      };
    }
  },

  createChatRoom: async (roomType: 'private' | 'group' | 'anonymous', otherUserId?: number, name?: string): Promise<ApiResponse<ChatRoom>> => {
    try {
      const response = await api.post<ChatRoom>('/chat/rooms/', {
        room_type: roomType,
        other_user_id: otherUserId,
        name: name,
      });
      return { success: true, data: response.data };
    } catch (error) {
      const axiosError = error as AxiosError;
      return { 
        success: false, 
        error: (axiosError.response?.data as any)?.message || 'Failed to create chat room' 
      };
    }
  },

  getMessages: async (roomId: number): Promise<ApiResponse<Message[]>> => {
    try {
      const response = await api.get<Message[]>(`/chat/rooms/${roomId}/messages/`);
      return { success: true, data: response.data };
    } catch (error) {
      const axiosError = error as AxiosError;
      return { 
        success: false, 
        error: (axiosError.response?.data as any)?.message || 'Failed to get messages' 
      };
    }
  },
};

export default api;