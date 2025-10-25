import React from 'react';
import { type ChatRoom as ChatRoomType } from '../services/api';

interface ChatRoomProps {
  room: ChatRoomType;
  isActive: boolean;
  onClick: () => void;
}

const ChatRoomComponent: React.FC<ChatRoomProps> = ({ room, isActive, onClick }) => {
  const formatLastMessageTime = (timestamp?: string) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString();
    }
  };

  const getRoomDisplayName = () => {
    if (room.room_type === 'anonymous') {
      return 'Anonymous Chat';
    }
    return room.name || `Room ${room.id}`;
  };

  return (
    <div
      className={`p-3 cursor-pointer border-b border-gray-200 hover:bg-gray-50 ${
        isActive ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
      }`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <h3 className={`text-sm font-medium truncate ${
            isActive ? 'text-blue-900' : 'text-gray-900'
          }`}>
            {getRoomDisplayName()}
          </h3>
          {room.last_message && (
            <p className={`text-xs truncate mt-1 ${
              isActive ? 'text-blue-700' : 'text-gray-500'
            }`}>
              {room.last_message.content}
            </p>
          )}
        </div>
        <div className="flex flex-col items-end">
          <span className={`text-xs ${
            isActive ? 'text-blue-600' : 'text-gray-400'
          }`}>
            {formatLastMessageTime(room.last_message?.timestamp)}
          </span>
          {room.room_type === 'anonymous' && (
            <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full mt-1">
              Anonymous
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatRoomComponent;
