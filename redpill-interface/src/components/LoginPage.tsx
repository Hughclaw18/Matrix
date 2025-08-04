import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface LoginPageProps {
  onLogin: () => void;
}

export const LoginPage = ({ onLogin }: LoginPageProps) => {
  const [selectedPill, setSelectedPill] = useState<'red' | 'blue' | null>(null);
  const [showChoice, setShowChoice] = useState(false);

  const handlePillChoice = (pill: 'red' | 'blue') => {
    setSelectedPill(pill);
    if (pill === 'red') {
      setTimeout(() => {
        onLogin();
      }, 2000);
    } else {
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    }
  };

  return (
    <div className="min-h-screen bg-background relative dark flex items-center justify-center crt-monitor">
      <div className="scan-line" />
      <div className="digital-rain" />
      
      <Card className="matrix-terminal p-8 max-w-2xl mx-4 text-center relative">
        <div className="glitch-effect"></div>
        
        {!showChoice ? (
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
              className="matrix-border bg-primary hover:bg-primary/80 text-primary-foreground font-mono"
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
                  className="w-20 h-20 rounded-full bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_20px_#3b82f6] hover:shadow-[0_0_30px_#3b82f6] transition-all duration-300"
                  disabled={selectedPill !== null}
                >
                  <div className="w-12 h-12 bg-blue-500 rounded-full shadow-inner"></div>
                </Button>
                <p className="mt-2 text-sm font-mono text-muted-foreground">Blue Pill</p>
              </div>

              <div className="text-center">
                <Button
                  onClick={() => handlePillChoice('red')}
                  className="w-20 h-20 rounded-full bg-red-600 hover:bg-red-500 text-white shadow-[0_0_20px_#ef4444] hover:shadow-[0_0_30px_#ef4444] transition-all duration-300"
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
      </Card>
    </div>
  );
};