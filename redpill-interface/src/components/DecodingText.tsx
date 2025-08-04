import { useState, useEffect } from 'react';

interface DecodingTextProps {
  text: string;
  speed?: number;
  className?: string;
  showCursorAfter?: boolean;
}

export const DecodingText = ({ text, speed = 50, className = '', showCursorAfter = false }: DecodingTextProps) => {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isDecoding, setIsDecoding] = useState(true);

  const glyphs = 'ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ0123456789@#$%^&*';

  useEffect(() => {
    if (currentIndex < text.length) {
      const interval = setInterval(() => {
        setDisplayText(prev => {
          if (currentIndex < text.length) {
            // Generate random glyphs for positions that haven't been revealed yet
            let newText = prev.slice(0, currentIndex);
            
            // Add the current character
            newText += text[currentIndex];
            
            // Add random glyphs for upcoming positions
            for (let i = currentIndex + 1; i < Math.min(text.length, currentIndex + 10); i++) {
              if (text[i] === ' ') {
                newText += ' ';
              } else {
                newText += glyphs[Math.floor(Math.random() * glyphs.length)];
              }
            }
            
            return newText;
          }
          return prev;
        });

        setCurrentIndex(prev => prev + 1);
      }, speed);

      return () => clearInterval(interval);
    } else {
      setIsDecoding(false);
      setDisplayText(text);
    }
  }, [currentIndex, text, speed]);

  return (
    <span className={`font-mono ${className}`}>
      {displayText}
      {isDecoding && (
        <span className="animate-pulse text-primary">|</span>
      )}
      {!isDecoding && showCursorAfter && (
        <span className="animate-pulse text-primary">_</span>
      )}
    </span>
  );
};