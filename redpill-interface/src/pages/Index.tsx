import { useState } from 'react';
import { ChatInterface } from '@/components/ChatInterface';
import { LoginPage } from '@/components/LoginPage';

const Index = () => {
  const [user, setUser] = useState<{ id: number; username: string } | null>(() => {
    const saved = localStorage.getItem('matrix_user');
    return saved ? JSON.parse(saved) : null;
  });

  const handleLogin = (id: number, username: string) => {
    const userData = { id, username };
    setUser(userData);
    localStorage.setItem('matrix_user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('matrix_user');
  };

  if (!user) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return <ChatInterface user={user} onLogout={handleLogout} />;
};

export default Index;