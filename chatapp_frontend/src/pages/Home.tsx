import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { chatAPI } from '../services/api';
import { isAuthenticated } from '../utils/auth';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [showAnonymousModal, setShowAnonymousModal] = useState(false);
  const [anonymousName, setAnonymousName] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAnonymousChat = async () => {
    if (!anonymousName.trim()) return;

    setLoading(true);
    try {
      const response = await chatAPI.createChatRoom('anonymous');
      if (response.success && response.data) {
        navigate(`/chat/anonymous/${response.data.id}?name=${encodeURIComponent(anonymousName)}`);
      }
    } catch (error) {
      console.error('Failed to create anonymous chat:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">ChatFast</h1>
          <p className="text-lg text-gray-600 mb-8">Connect with friends and chat anonymously</p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="space-y-6">
            {isAuthenticated() ? (
              <>
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Welcome back!</h2>
                  <p className="text-gray-600 mb-6">What would you like to do?</p>
                </div>
                
                <div className="space-y-4">
                  <button
                    onClick={() => navigate('/chat')}
                    className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Go to Chat
                  </button>
                  
                  <button
                    onClick={() => navigate('/friends')}
                    className="w-full flex justify-center py-3 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Manage Friends
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Get Started</h2>
                  <p className="text-gray-600 mb-6">Sign in to your account or create a new one</p>
                </div>
                
                <div className="space-y-4">
                  <button
                    onClick={() => navigate('/login')}
                    className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Sign In
                  </button>
                  
                  <button
                    onClick={() => navigate('/register')}
                    className="w-full flex justify-center py-3 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Create Account
                  </button>
                </div>
              </>
            )}

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Or</span>
              </div>
            </div>

            <button
              onClick={() => setShowAnonymousModal(true)}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
            >
              Join Anonymous Chat
            </button>
          </div>
        </div>
      </div>

      {/* Anonymous Chat Modal */}
      {showAnonymousModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Enter Anonymous Name</h3>
              <input
                type="text"
                value={anonymousName}
                onChange={(e) => setAnonymousName(e.target.value)}
                placeholder="Your anonymous name..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 mb-4"
                maxLength={20}
              />
              <div className="flex space-x-3">
                <button
                  onClick={handleAnonymousChat}
                  disabled={!anonymousName.trim() || loading}
                  className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Creating...' : 'Join Chat'}
                </button>
                <button
                  onClick={() => {
                    setShowAnonymousModal(false);
                    setAnonymousName('');
                  }}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Home;

