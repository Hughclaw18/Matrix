import { useState, useRef } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';

interface LoginPageProps {
  onLogin: (id: number, username: string) => void;
}

export const LoginPage = ({ onLogin }: LoginPageProps) => {
  const [selectedPill, setSelectedPill] = useState<'red' | 'blue' | null>(null);
  const [showChoice, setShowChoice] = useState(false);
  const [showVideo, setShowVideo] = useState(false);
  const [showTerminalForm, setShowTerminalForm] = useState(false);
  
  // Credentials states
  const [isSignUp, setIsSignUp] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);

  const handlePillChoice = (pill: 'red' | 'blue') => {
    setSelectedPill(pill);
    setShowVideo(true);
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      toast.error('Please enter both username and password.');
      return;
    }

    setIsLoading(true);
    const endpoint = isSignUp ? 'register' : 'login';
    try {
      const response = await axios.post(`http://localhost:8001/${endpoint}`, {
        username,
        password,
      });

      if (isSignUp) {
        toast.success('Access configuration initialized. You may now login.');
        setIsSignUp(false);
        setPassword('');
      } else {
        toast.success(`Access granted. Welcome, ${response.data.username}.`);
        onLogin(response.data.id, response.data.username);
      }
    } catch (error: any) {
      console.error(error);
      const detail = error.response?.data?.detail || 'System connection failure. Verify neural link.';
      toast.error(detail);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background relative dark flex items-center justify-center crt-monitor">
      <div className="scan-line" />
      <div className="digital-rain" />
      
      <Card className="matrix-terminal p-8 max-w-2xl mx-4 text-center relative w-full border-primary">
        <div className="glitch-effect"></div>
        
        {showTerminalForm ? (
          <div className="space-y-6 text-left">
            <div className="text-center mb-6">
              <h1 className="text-2xl font-bold font-mono text-primary matrix-glow">
                {isSignUp ? 'INITIALIZE NEW NEURAL CONFIG' : 'NEURAL LOG IN SEQUENCE'}
              </h1>
              <p className="text-xs text-muted-foreground font-mono mt-1">
                SECURE TRILOGY CONTEXT DECRYPTER v4.0
              </p>
            </div>

            <form onSubmit={handleAuthSubmit} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-mono text-primary">ACCESS IDENTITY (USERNAME)</label>
                <Input
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. Neo / Trinity"
                  className="font-mono matrix-border bg-black border-primary text-primary"
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-mono text-primary">SECURE PASSCODE (PASSWORD)</label>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="********"
                  className="font-mono matrix-border bg-black border-primary text-primary"
                  disabled={isLoading}
                />
              </div>

              <div className="pt-2 flex flex-col gap-2">
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="matrix-border bg-primary hover:bg-primary/80 text-black font-mono w-full"
                >
                  {isLoading ? 'EXECUTING...' : isSignUp ? 'CREATE CONFIGURATION' : 'DECRYPT ACCESS'}
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => {
                    setIsSignUp(!isSignUp);
                    setUsername('');
                    setPassword('');
                  }}
                  className="text-xs font-mono text-muted-foreground hover:text-primary hover:bg-transparent"
                  disabled={isLoading}
                >
                  {isSignUp ? 'Already registered? Login to link' : 'New operator? Initialize interface config'}
                </Button>
              </div>
            </form>
          </div>
        ) : !showChoice ? (
          <div className="space-y-6">
            <div className="matrix-glow">
              <h1 className="text-4xl font-bold font-mono text-primary mb-4">
                THE MATRIX
              </h1>
              <div className="typewriter-text">
                <p className="text-lg font-mono text-muted-foreground mb-6">
                  Neo... we've been waiting for you.
                </p>
                <p className="text-base font-mono text-foreground mb-8">
                  This is your last chance. After this, there is no going back.
                </p>
              </div>
            </div>
            
            <Button
              onClick={() => setShowChoice(true)}
              className="matrix-border bg-primary hover:bg-primary/80 text-black font-mono"
            >
              Enter the Matrix
            </Button>
          </div>
        ) : (
          <div className="space-y-8">
            <div className="text-center space-y-4">
              <h2 className="text-2xl font-bold font-mono text-primary matrix-glow">
                MORPHEUS
              </h2>
              <div className="typewriter-text space-y-4">
                <p className="text-base font-mono text-foreground">
                  You take the blue pill - the story ends, you wake up in your bed and believe whatever you want to believe.
                </p>
                <p className="text-base font-mono text-foreground">
                  You take the red pill - you stay in Wonderland, and I show you how deep the rabbit hole goes.
                </p>
              </div>
            </div>

            <div className="flex justify-center gap-8">
              <div className="text-center">
                <Button
                  onClick={() => handlePillChoice('blue')}
                  className="w-20 h-20 rounded-full bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_20px_#3b82f6] hover:shadow-[0_0_30px_#3b82f6] transition-all duration-300 flex items-center justify-center"
                  disabled={selectedPill !== null}
                >
                  <div className="w-12 h-12 bg-blue-500 rounded-full shadow-inner"></div>
                </Button>
                <p className="mt-2 text-sm font-mono text-muted-foreground">Blue Pill</p>
              </div>

              <div className="text-center">
                <Button
                  onClick={() => handlePillChoice('red')}
                  className="w-20 h-20 rounded-full bg-red-600 hover:bg-red-500 text-white shadow-[0_0_20px_#ef4444] hover:shadow-[0_0_30px_#ef4444] transition-all duration-300 flex items-center justify-center"
                  disabled={selectedPill !== null}
                >
                  <div className="w-12 h-12 bg-red-500 rounded-full shadow-inner"></div>
                </Button>
                <p className="mt-2 text-sm font-mono text-muted-foreground">Red Pill</p>
              </div>
            </div>

            {selectedPill && (
              <div className="text-center">
                <p className="text-lg font-mono text-primary matrix-glow animate-pulse">
                  {selectedPill === 'red' 
                    ? 'Welcome to the real world, Neo...' 
                    : 'Goodbye, Mr. Anderson...'}
                </p>
              </div>
            )}
          </div>
        )}

        {showVideo && (
          <div className="fixed inset-0 w-screen h-screen bg-black z-50 flex items-center justify-center">
            <video
              ref={videoRef}
              src={selectedPill === 'red' ? '/red_pill_video.mp4' : '/blue_pill_video.mp4'}
              autoPlay
              controls
              onEnded={() => {
                setShowVideo(false);
                if (selectedPill === 'red') {
                  setShowTerminalForm(true);
                } else {
                  window.location.reload();
                }
              }}
              className="w-full h-full object-cover"
            />
            <Button
              onClick={() => {
                setShowVideo(false);
                if (selectedPill === 'red') {
                  setShowTerminalForm(true);
                } else {
                  window.location.reload();
                }
              }}
              className="absolute bottom-8 right-8 bg-white text-black px-4 py-2 rounded-full"
            >
              Skip Video
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};