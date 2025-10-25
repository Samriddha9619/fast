import React from 'react';
import { useNavigate } from 'react-router-dom';
import AuthForm from '../components/AuthForm';
import { type AuthResponse } from '../services/api';
import { saveToken } from '../utils/auth';

const Login: React.FC = () => {
  const navigate = useNavigate();

  const handleSuccess = (data: AuthResponse) => {
    saveToken(data.token);
    navigate('/chat');
  };

  return <AuthForm isLogin={true} onSuccess={handleSuccess} />;
};

export default Login;
