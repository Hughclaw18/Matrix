import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { 
  Bold, 
  Italic, 
  Underline, 
  List, 
  ListOrdered, 
  Quote,
  Code,
  Undo,
  Redo,
  Copy,
  Save
} from 'lucide-react';
import { toast } from 'sonner';

interface TextEditorProps {
  content?: string;
  onChange?: (content: string) => void;
  readOnly?: boolean;
}

export const TextEditor = ({ content = '', onChange, readOnly = false }: TextEditorProps) => {
  const [editorContent, setEditorContent] = useState(content);
  const editorRef = useRef<HTMLDivElement>(null);

  const executeCommand = (command: string, value?: string) => {
    document.execCommand(command, false, value);
    const newContent = editorRef.current?.innerHTML || '';
    setEditorContent(newContent);
    onChange?.(newContent);
  };

  const handleContentChange = () => {
    const newContent = editorRef.current?.innerHTML || '';
    setEditorContent(newContent);
    onChange?.(newContent);
  };

  const copyToClipboard = async () => {
    try {
      const textContent = editorRef.current?.innerText || '';
      await navigator.clipboard.writeText(textContent);
      toast.success('Content copied to clipboard');
    } catch (error) {
      toast.error('Failed to copy content');
    }
  };

  const saveContent = () => {
    const textContent = editorRef.current?.innerText || '';
    const blob = new Blob([textContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ai-response.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('Content saved as file');
  };

  return (
    <Card className="matrix-terminal">
      {!readOnly && (
        <>
          <div className="flex flex-wrap gap-1 p-2 border-b border-border">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => executeCommand('bold')}
              className="matrix-border"
            >
              <Bold className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => executeCommand('italic')}
              className="matrix-border"
            >
              <Italic className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => executeCommand('underline')}
              className="matrix-border"
            >
              <Underline className="w-4 h-4" />
            </Button>
            
            <Separator orientation="vertical" className="h-8" />
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => executeCommand('insertUnorderedList')}
              className="matrix-border"
            >
              <List className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => executeCommand('insertOrderedList')}
              className="matrix-border"
            >
              <ListOrdered className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => executeCommand('formatBlock', 'blockquote')}
              className="matrix-border"
            >
              <Quote className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => executeCommand('formatBlock', 'pre')}
              className="matrix-border"
            >
              <Code className="w-4 h-4" />
            </Button>
            
            <Separator orientation="vertical" className="h-8" />
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => executeCommand('undo')}
              className="matrix-border"
            >
              <Undo className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => executeCommand('redo')}
              className="matrix-border"
            >
              <Redo className="w-4 h-4" />
            </Button>
          </div>
        </>
      )}
      
      <div className="flex justify-end gap-2 p-2 border-b border-border">
        <Button
          variant="ghost"
          size="sm"
          onClick={copyToClipboard}
          className="matrix-border"
        >
          <Copy className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={saveContent}
          className="matrix-border"
        >
          <Save className="w-4 h-4" />
        </Button>
      </div>
      
      <div
        ref={editorRef}
        contentEditable={!readOnly}
        onInput={handleContentChange}
        className="p-4 min-h-[200px] outline-none font-mono text-sm matrix-glow overflow-y-auto scrollbar-matrix"
      />
    </Card>
  );
};