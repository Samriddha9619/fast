import React, { useState, useEffect } from 'react';
import { userAPI, type UserSearchResult } from '../services/api';

interface UserSearchProps {
  onUserAction: (userId: number, action: 'add' | 'accept' | 'reject') => void;
  onStartChat: (userId: number) => void;
}

const UserSearch: React.FC<UserSearchProps> = ({ onUserAction, onStartChat }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<UserSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const searchUsers = async () => {
      if (query.trim().length < 2) {
        setResults([]);
        return;
      }

      setLoading(true);
      setError('');
      
      try {
        const response = await userAPI.searchUsers(query);
        if (response.success && response.data) {
          setResults(response.data);
        } else {
          setError(response.error || 'Search failed');
        }
      } catch (err) {
        setError('An unexpected error occurred');
      } finally {
        setLoading(false);
      }
    };

    const debounceTimer = setTimeout(searchUsers, 300);
    return () => clearTimeout(debounceTimer);
  }, [query]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'friend':
        return <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">Friends</span>;
      case 'request_sent':
        return <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">Request Sent</span>;
      case 'request_received':
        return <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">Request Received</span>;
      default:
        return null;
    }
  };

  const getActionButton = (user: UserSearchResult) => {
    switch (user.friendship_status) {
      case 'none':
        return (
          <button
            onClick={() => onUserAction(user.id, 'add')}
            className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Add Friend
          </button>
        );
      case 'request_received':
        return (
          <div className="flex space-x-2">
            <button
              onClick={() => onUserAction(user.id, 'accept')}
              className="px-3 py-1 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              Accept
            </button>
            <button
              onClick={() => onUserAction(user.id, 'reject')}
              className="px-3 py-1 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              Reject
            </button>
          </div>
        );
      case 'friend':
        return (
          <button
            onClick={() => onStartChat(user.id)}
            className="px-3 py-1 bg-gray-600 text-white text-sm rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            Chat
          </button>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
          Search Users
        </label>
        <div className="relative">
          <input
            type="text"
            id="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by username or email..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {loading && (
            <div className="absolute right-3 top-2.5">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="text-red-600 text-sm">{error}</div>
      )}

      {results.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-700">Search Results</h3>
          {results.map((user) => (
            <div
              key={user.id}
              className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200"
            >
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-900">{user.username}</h4>
                  <p className="text-xs text-gray-500">{user.email}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {getStatusBadge(user.friendship_status)}
                {getActionButton(user)}
              </div>
            </div>
          ))}
        </div>
      )}

      {query.length > 0 && results.length === 0 && !loading && !error && (
        <div className="text-center py-4">
          <p className="text-gray-500">No users found matching "{query}"</p>
        </div>
      )}
    </div>
  );
};

export default UserSearch;
