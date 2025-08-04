import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Card } from '@/components/ui/card';
import { User, Bot } from 'lucide-react';
import { DecodingText } from './DecodingText';

interface ChatMessageProps {
  message: string;
  isUser: boolean;
  timestamp: Date;
  files?: File[];
  isLastMessage?: boolean;
}

export const ChatMessage = ({ message, isUser, timestamp, files, isLastMessage = false }: ChatMessageProps) => {
  return (
    <div className={`flex gap-3 mb-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <Avatar className="w-8 h-8 matrix-border">
        <AvatarFallback className={`${isUser ? 'bg-secondary' : 'bg-primary'} ${isUser ? 'text-secondary-foreground' : 'text-primary-foreground'}`}>
          {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
        </AvatarFallback>
      </Avatar>
      
      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[70%]`}>
        <Card className={`p-3 matrix-terminal ${isUser ? 'bg-secondary' : 'bg-card'}`}>
          <div className="whitespace-pre-wrap font-mono text-sm matrix-glow">
            {isUser ? (
              message
            ) : (
              <DecodingText text={message} speed={30} className="text-primary" showCursorAfter={isLastMessage} />
            )}
          </div>
          
          {files && files.length > 0 && (
            <div className="mt-2 space-y-1">
              {files.map((file, index) => (
                <div key={index} className="text-xs text-muted-foreground bg-muted p-2 rounded border matrix-border">
                  📎 {file.name} ({(file.size / 1024).toFixed(1)} KB)
                </div>
              ))}
            </div>
          )}
        </Card>
        
        <span className="text-xs text-muted-foreground mt-1 font-mono">
          {timestamp.toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
};