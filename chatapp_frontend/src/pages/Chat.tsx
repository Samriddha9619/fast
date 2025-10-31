import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { chatAPI, authAPI, type ChatRoom, type Message, type User } from '../services/api';
import { getToken } from '../utils/auth';
import ChatRoomComponent from '../components/ChatRoom';
import ChatMessage from '../components/ChatMessage';
import WebSocketService from '../services/websocket';

const Chat: React.FC = () => {
  const navigate = useNavigate();
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

      const token = getToken();
      WebSocketService.connect(token, isAnonymous);

      WebSocketService.onMessage((data) => {
        if (data.type === 'new_message' && data.message) {
          setMessages(prev => [...prev, data.message]);
        } else if (data.type === 'user_typing') {
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

    if (isAnonymous) {
      WebSocketService.sendTyping(selectedRoom.id, true, anonymousName);
    } else {
      WebSocketService.sendTyping(selectedRoom.id, true);
    }

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

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

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ animation: 'spin 1s linear infinite', borderRadius: '50%', height: '48px', width: '48px', borderBottom: '2px solid #2563eb' }}></div>
      </div>
    );
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#f9fafb' }}>
      {/* Navigation Bar */}
      <nav style={{
        backgroundColor: '#1f2937',
        color: 'white',
        padding: '0 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        height: '60px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <Link to="/" style={{ 
            fontSize: '1.5rem', 
            fontWeight: 'bold',
            color: 'white',
            textDecoration: 'none'
          }}>
            ChatFast
          </Link>
          
          <div style={{ display: 'flex', gap: '1.5rem' }}>
            <Link to="/chat" style={{
              color: 'white',
              textDecoration: 'none',
              padding: '0.5rem 0',
              borderBottom: '2px solid #2563eb',
              fontWeight: '500'
            }}>
              Chat
            </Link>
            {!isAnonymous && (
              <Link to="/friends" style={{
                color: '#d1d5db',
                textDecoration: 'none',
                padding: '0.5rem 0',
                fontWeight: '500',
                transition: 'color 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.color = 'white'}
              onMouseLeave={(e) => e.currentTarget.style.color = '#d1d5db'}
              >
                Friends
              </Link>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {currentUser && !isAnonymous && (
            <span style={{ fontSize: '0.875rem', color: '#d1d5db' }}>
              {currentUser.username}
            </span>
          )}
          {isAnonymous && (
            <span style={{ fontSize: '0.875rem', color: '#d1d5db' }}>
              {anonymousName}
            </span>
          )}
          <button
            onClick={handleLogout}
            style={{
              backgroundColor: '#dc2626',
              color: 'white',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '0.375rem',
              cursor: 'pointer',
              fontWeight: '500',
              fontSize: '0.875rem'
            }}
          >
            {isAnonymous ? 'Exit' : 'Logout'}
          </button>
        </div>
      </nav>

      {/* Main Chat Container */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <div style={{ width: '256px', backgroundColor: 'white', borderRight: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '1rem', borderBottom: '1px solid #e5e7eb' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#111827', margin: 0 }}>
              {isAnonymous ? 'Anonymous Chat' : 'Chat Rooms'}
            </h2>
          </div>
          
          <div style={{ flex: 1, overflowY: 'auto' }}>
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
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {selectedRoom ? (
            <>
              {/* Chat Header */}
              <div style={{ backgroundColor: 'white', borderBottom: '1px solid #e5e7eb', padding: '1rem' }}>
                <h2 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#111827', margin: 0 }}>
                  {isAnonymous ? 'Anonymous Chat' : selectedRoom.name || `Room ${selectedRoom.id}`}
                </h2>
                {isAnonymous && (
                  <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>You are: {anonymousName}</p>
                )}
              </div>

              {/* Messages */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', backgroundColor: '#f9fafb' }}>
                {messages.length === 0 ? (
                  <div style={{ textAlign: 'center', color: '#6b7280', marginTop: '2rem' }}>
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
                  <div style={{ fontSize: '0.875rem', color: '#6b7280', fontStyle: 'italic', marginTop: '0.5rem' }}>
                    {typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Message Input */}
              <div style={{ backgroundColor: 'white', borderTop: '1px solid #e5e7eb', padding: '1rem' }}>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <input
                    type="text"
                    value={newMessage}
                    onChange={handleTyping}
                    onKeyPress={handleKeyPress}
                    placeholder="Type a message..."
                    style={{
                      flex: 1,
                      padding: '0.5rem 0.75rem',
                      border: '1px solid #d1d5db',
                      borderRadius: '0.375rem',
                      outline: 'none',
                      fontSize: '0.875rem'
                    }}
                  />
                  <button
                    onClick={sendMessage}
                    disabled={!newMessage.trim()}
                    style={{
                      padding: '0.5rem 1.5rem',
                      backgroundColor: newMessage.trim() ? '#2563eb' : '#9ca3af',
                      color: 'white',
                      border: 'none',
                      borderRadius: '0.375rem',
                      cursor: newMessage.trim() ? 'pointer' : 'not-allowed',
                      fontWeight: '500',
                      fontSize: '0.875rem'
                    }}
                  >
                    Send
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f9fafb' }}>
              <div style={{ textAlign: 'center' }}>
                <h3 style={{ fontSize: '1.125rem', fontWeight: '500', color: '#111827', marginBottom: '0.5rem' }}>No room selected</h3>
                <p style={{ color: '#6b7280' }}>Choose a room from the sidebar to start chatting</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div style={{
          position: 'fixed',
          bottom: '1rem',
          right: '1rem',
          backgroundColor: '#fee2e2',
          border: '1px solid #f87171',
          color: '#b91c1c',
          padding: '0.75rem 1rem',
          borderRadius: '0.375rem',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          {error}
        </div>
      )}
    </div>
  );
};

export default Chat;