import { useState } from 'react';
import { ChatInterface } from '@/components/ChatInterface';
import { LoginPage } from '@/components/LoginPage';

const Index = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  if (!isLoggedIn) {
    return <LoginPage onLogin={() => setIsLoggedIn(true)} />;
  }

  return <ChatInterface />;
};

export default Index;