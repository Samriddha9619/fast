import React from 'react';
import { useNavigate } from 'react-router-dom';
import AuthForm from '../components/AuthForm';
import { type AuthResponse } from '../services/api';

const Register: React.FC = () => {
  const navigate = useNavigate();

  const handleSuccess = (_data: any) => {
    // Don't save token here, let user login manually
    navigate('/login');
  };

  return <AuthForm isLogin={false} onSuccess={handleSuccess} />;
};

export default Register;
