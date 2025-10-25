import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { chatAPI, authAPI, type ChatRoom, type Message, type User } from '../services/api';
import { getToken } from '../utils/auth';
import ChatRoomComponent from '../components/ChatRoom';
import ChatMessage from '../components/ChatMessage';
import WebSocketService from '../services/websocket';

const Chat: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [rooms, setRooms] = useState<ChatRoom[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<ChatRoom | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [anonymousName, setAnonymousName] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    loadInitialData();
    
    // Check if this is an anonymous chat
    const pathname = window.location.pathname;
    if (pathname.includes('/anonymous/') || searchParams.get('name')) {
      setIsAnonymous(true);
      setAnonymousName(searchParams.get('name') || 'Anonymous');
    }

    return () => {
      WebSocketService.disconnect();
    };
  }, []);

  useEffect(() => {
    if (selectedRoom) {
      loadMessages(selectedRoom.id);
      joinRoom(selectedRoom.id);
    }
  }, [selectedRoom]);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    scrollToBottom();
  }, [messages]);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [profileRes, roomsRes] = await Promise.all([
        authAPI.getProfile(),
        chatAPI.getChatRooms()
      ]);

      if (profileRes.success && profileRes.data) {
        setCurrentUser(profileRes.data);
      }

      if (roomsRes.success && roomsRes.data) {
        setRooms(roomsRes.data);
        
        // Check if there's a specific room to select
        const roomId = searchParams.get('room');
        if (roomId) {
          const room = roomsRes.data.find(r => r.id === parseInt(roomId));
          if (room) {
            setSelectedRoom(room);
          }
        } else if (roomsRes.data.length > 0) {
          setSelectedRoom(roomsRes.data[0]);
        }
      }

      // Connect WebSocket
      const token = getToken();
      WebSocketService.connect(token, isAnonymous);

      // Set up WebSocket listeners
      WebSocketService.onMessage((data) => {
        if (data.type === 'new_message' && data.message) {
          setMessages(prev => [...prev, data.message]);
        } else if (data.type === 'user_typing') {
          // Handle typing indicators
          if (data.is_typing) {
            setTypingUsers(prev => [...new Set([...prev, data.anonymous_name || 'Someone'])]);
          } else {
            setTypingUsers(prev => prev.filter(name => name !== (data.anonymous_name || 'Someone')));
          }
        }
      });

      WebSocketService.onError((error) => {
        console.error('WebSocket error:', error);
        setError('Connection error. Please refresh the page.');
      });

    } catch (err) {
      setError('Failed to load chat data');
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (roomId: number) => {
    try {
      const response = await chatAPI.getMessages(roomId);
      if (response.success && response.data) {
        setMessages(response.data);
      }
    } catch (err) {
      console.error('Failed to load messages:', err);
    }
  };

  const joinRoom = (roomId: number) => {
    if (isAnonymous) {
      WebSocketService.joinRoom(roomId, anonymousName);
    } else {
      WebSocketService.joinRoom(roomId);
    }
  };

  const sendMessage = () => {
    if (!newMessage.trim() || !selectedRoom) return;

    if (isAnonymous) {
      WebSocketService.sendMessage(selectedRoom.id, newMessage, anonymousName);
    } else {
      WebSocketService.sendMessage(selectedRoom.id, newMessage);
    }

    setNewMessage('');
  };

  const handleTyping = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNewMessage(e.target.value);

    if (!selectedRoom) return;

    // Send typing indicator
    if (isAnonymous) {
      WebSocketService.sendTyping(selectedRoom.id, true, anonymousName);
    } else {
      WebSocketService.sendTyping(selectedRoom.id, true);
    }

    // Clear previous timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Set new timeout to stop typing indicator
    typingTimeoutRef.current = setTimeout(() => {
      if (isAnonymous) {
        WebSocketService.sendTyping(selectedRoom.id, false, anonymousName);
      } else {
        WebSocketService.sendTyping(selectedRoom.id, false);
      }
    }, 1000);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900">
            {isAnonymous ? 'Anonymous Chat' : 'Chat Rooms'}
          </h1>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {rooms.map((room) => (
            <ChatRoomComponent
              key={room.id}
              room={room}
              isActive={selectedRoom?.id === room.id}
              onClick={() => setSelectedRoom(room)}
            />
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedRoom ? (
          <>
            {/* Chat Header */}
            <div className="bg-white border-b border-gray-200 p-4">
              <h2 className="text-lg font-semibold text-gray-900">
                {isAnonymous ? 'Anonymous Chat' : selectedRoom.name || `Room ${selectedRoom.id}`}
              </h2>
              {isAnonymous && (
                <p className="text-sm text-gray-500">You are: {anonymousName}</p>
              )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 mt-8">
                  <p>No messages yet. Start the conversation!</p>
                </div>
              ) : (
                messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                    currentUser={currentUser}
                    isAnonymous={isAnonymous}
                  />
                ))
              )}
              
              {/* Typing Indicator */}
              {typingUsers.length > 0 && (
                <div className="text-sm text-gray-500 italic">
                  {typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input */}
            <div className="bg-white border-t border-gray-200 p-4">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={newMessage}
                  onChange={handleTyping}
                  onKeyPress={handleKeyPress}
                  placeholder="Type a message..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <button
                  onClick={sendMessage}
                  disabled={!newMessage.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Send
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-2">No room selected</h3>
              <p className="text-gray-500">Choose a room from the sidebar to start chatting</p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="fixed bottom-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
    </div>
  );
};

export default Chat;