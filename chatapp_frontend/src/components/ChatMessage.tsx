import React from 'react';
import { type Message, type User } from '../services/api';

interface ChatMessageProps {
  message: Message;
  currentUser: User | null;
  isAnonymous?: boolean;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, currentUser, isAnonymous = false }) => {
  const isOwnMessage = currentUser && message.sender.id === currentUser.id;
  const isAnonymousMessage = isAnonymous || !!message.anonymous_name;

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getDisplayName = () => {
    if (isAnonymousMessage) {
      return message.anonymous_name || 'Anonymous';
    }
    return message.sender.username;
  };

  return (
    <div className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
        isOwnMessage 
          ? 'bg-blue-500 text-white' 
          : 'bg-gray-200 text-gray-800'
      }`}>
        <div className="flex items-center space-x-2 mb-1">
          {isAnonymousMessage && (
            <span className="text-xs bg-gray-400 text-white px-2 py-1 rounded-full">
              Anon
            </span>
          )}
          <span className={`text-xs font-medium ${
            isOwnMessage ? 'text-blue-100' : 'text-gray-600'
          }`}>
            {getDisplayName()}
          </span>
        </div>
        <p className="text-sm">{message.content}</p>
        <p className={`text-xs mt-1 ${
          isOwnMessage ? 'text-blue-100' : 'text-gray-500'
        }`}>
          {formatTime(message.timestamp)}
        </p>
      </div>
    </div>
  );
};

export default ChatMessage;
