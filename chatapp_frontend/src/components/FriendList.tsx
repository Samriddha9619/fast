import React from 'react';
import { type Friendship, type User } from '../services/api';

interface FriendListProps {
  friends: Friendship[];
  currentUser: User | null;
  onStartChat: (friendId: number) => void;
}

const FriendList: React.FC<FriendListProps> = ({ friends, currentUser, onStartChat }) => {
  const getFriendUser = (friendship: Friendship): User => {
    return currentUser && friendship.user1.id === currentUser.id 
      ? friendship.user2 
      : friendship.user1;
  };

  if (friends.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-gray-400 mb-4">
          <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No friends yet</h3>
        <p className="text-gray-500">Start by adding some friends to begin chatting!</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {friends.map((friendship) => {
        const friend = getFriendUser(friendship);
        return (
          <div
            key={friendship.id}
            className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200 hover:bg-gray-50"
          >
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
                {friend.username.charAt(0).toUpperCase()}
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-900">{friend.username}</h3>
                <p className="text-xs text-gray-500">{friend.email}</p>
              </div>
            </div>
            <button
              onClick={() => onStartChat(friend.id)}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Chat
            </button>
          </div>
        );
      })}
    </div>
  );
};

export default FriendList;
