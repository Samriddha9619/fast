import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { friendAPI, chatAPI, type Friendship, type FriendRequest } from '../services/api';
import { authAPI, type User } from '../services/api';
import UserSearch from '../components/UserSearch';
import FriendList from '../components/FriendList';

const Friends: React.FC = () => {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [friends, setFriends] = useState<Friendship[]>([]);
  const [friendRequests, setFriendRequests] = useState<FriendRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [profileRes, friendsRes, requestsRes] = await Promise.all([
        authAPI.getProfile(),
        friendAPI.getFriends(),
        friendAPI.getFriendRequests()
      ]);

      if (profileRes.success && profileRes.data) {
        setCurrentUser(profileRes.data);
      }

      if (friendsRes.success && friendsRes.data) {
        setFriends(friendsRes.data);
      }

      if (requestsRes.success && requestsRes.data) {
        setFriendRequests(requestsRes.data);
      }
    } catch (err) {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleUserAction = async (userId: number, action: 'add' | 'accept' | 'reject') => {
    try {
      if (action === 'add') {
        const response = await friendAPI.sendFriendRequest(userId);
        if (response.success) {
          // Refresh the page to update search results
          window.location.reload();
        } else {
          setError(response.error || 'Failed to send friend request');
        }
      } else {
        // Find the request ID for this user
        const request = friendRequests.find(req => 
          action === 'accept' ? req.sender.id === userId : req.sender.id === userId
        );
        
        if (request) {
          const response = await friendAPI.respondFriendRequest(
            request.id, 
            action === 'accept' ? 'accept' : 'reject'
          );
          
          if (response.success) {
            // Remove the request from the list
            setFriendRequests(prev => prev.filter(req => req.id !== request.id));
            // Refresh friends list
            loadData();
          } else {
            setError(response.error || 'Failed to respond to friend request');
          }
        }
      }
    } catch (err) {
      setError('An unexpected error occurred');
    }
  };

  const handleStartChat = async (friendId: number) => {
    try {
      const response = await chatAPI.createChatRoom('private', friendId);
      if (response.success && response.data) {
        navigate(`/chat?room=${response.data.id}`);
      } else {
        setError(response.error || 'Failed to create chat room');
      }
    } catch (err) {
      setError('An unexpected error occurred');
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
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Friends</h1>
            <p className="mt-2 text-gray-600">Manage your friends and find new people to chat with</p>
          </div>

          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
              <div className="text-red-800">{error}</div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* User Search */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">Find Friends</h2>
                <UserSearch onUserAction={handleUserAction} onStartChat={handleStartChat} />
              </div>
            </div>

            {/* Friend Requests */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">Friend Requests</h2>
                {friendRequests.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-gray-400 mb-4">
                      <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <p className="text-gray-500">No pending friend requests</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {friendRequests.map((request) => (
                      <div key={request.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
                            {request.sender.username.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <h3 className="text-sm font-medium text-gray-900">{request.sender.username}</h3>
                            <p className="text-xs text-gray-500">{request.sender.email}</p>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleUserAction(request.sender.id, 'accept')}
                            className="px-3 py-1 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
                          >
                            Accept
                          </button>
                          <button
                            onClick={() => handleUserAction(request.sender.id, 'reject')}
                            className="px-3 py-1 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                          >
                            Reject
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Friends List */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">Your Friends</h2>
                <FriendList 
                  friends={friends} 
                  currentUser={currentUser} 
                  onStartChat={handleStartChat} 
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Friends;
