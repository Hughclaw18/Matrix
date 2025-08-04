import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Mic, MicOff, Square } from 'lucide-react';
import { toast } from 'sonner';

// Extend Window interface for speech recognition
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

interface SpeechToTextProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export const SpeechToText = ({ onTranscript, disabled }: SpeechToTextProps) => {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Check if speech recognition is supported
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      setIsSupported(true);
      recognitionRef.current = new SpeechRecognition();
      
      const recognition = recognitionRef.current;
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
        toast.success('Speech recognition started');
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.onresult = (event) => {
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        
        if (finalTranscript) {
          onTranscript(finalTranscript);
        }
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        toast.error(`Speech recognition error: ${event.error}`);
      };
    } else {
      setIsSupported(false);
      toast.error('Speech recognition not supported in this browser');
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [onTranscript]);

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      recognitionRef.current.start();
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  };

  if (!isSupported) {
    return (
      <Button variant="ghost" size="sm" disabled className="matrix-border">
        <MicOff className="w-4 h-4" />
      </Button>
    );
  }

  return (
    <Button
      variant={isListening ? "destructive" : "ghost"}
      size="sm"
      onClick={isListening ? stopListening : startListening}
      disabled={disabled}
      className={`matrix-border transition-all duration-200 ${
        isListening ? 'matrix-glow animate-pulse' : ''
      }`}
    >
      {isListening ? <Square className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
    </Button>
  );
};