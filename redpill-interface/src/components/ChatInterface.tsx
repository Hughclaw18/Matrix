import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Send, 
  Paperclip, 
  Settings, 
  Maximize2, 
  Plus, 
  Trash2, 
  Edit3, 
  User, 
  LogOut, 
  MessageSquare,
  ArrowLeft,
  X
} from 'lucide-react';
import { ChatMessage } from './ChatMessage';
import { FileUpload } from './FileUpload';
import { SpeechToText } from './SpeechToText';
import { TextEditor } from './TextEditor';
import { GraphView } from './GraphView';

interface UserInfo {
  id: number;
  username: string;
}

interface ChatInterfaceProps {
  user: UserInfo;
  onLogout: () => void;
}

interface Session {
  id: number;
  name: string | null;
  timestamp: string;
}

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  files?: string[]; // we can display local file references or names
}

export const ChatInterface = ({ user, onLogout }: ChatInterfaceProps) => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  
  const [inputText, setInputText] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [editorContent, setEditorContent] = useState('');
  
  // Model selection states
  const [provider, setProvider] = useState<'Gemini' | 'NVIDIA' | 'Groq'>('Gemini');
  const [modelName, setModelName] = useState<string>('models/gemini-2.5-flash');
  
  // Profile view state
  const [view, setView] = useState<'chat' | 'profile'>('chat');
  const [fullName, setFullName] = useState('');
  const [dob, setDob] = useState('');
  const [email, setEmail] = useState('');
  const [profilePicPath, setProfilePicPath] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isProfileUpdating, setIsProfileUpdating] = useState(false);
  
  // Session naming states
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameText, setRenameText] = useState('');

  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Fetch all sessions on mount and whenever user changes
  useEffect(() => {
    fetchSessions();
  }, [user.id]);

  // Scroll to bottom when messages list updates
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const fetchSessions = async () => {
    try {
      const response = await axios.get(`http://localhost:8001/sessions?user_id=${user.id}`);
      const sessionList = response.data.sessions;
      setSessions(sessionList);
      
      // Auto-select the first session if nothing is selected yet
      if (sessionList.length > 0 && currentSessionId === null) {
        selectSession(sessionList[0].id);
      }
    } catch (err) {
      console.error('Error fetching sessions:', err);
      toast.error('Failed to load neural connections (chat sessions).');
    }
  };

  const selectSession = async (sessionId: number) => {
    setCurrentSessionId(sessionId);
    setIsRenaming(false);
    try {
      const response = await axios.get(`http://localhost:8001/sessions/${sessionId}/messages`);
      const messageList = response.data.messages;
      
      const formattedMessages: Message[] = messageList.map((m: any, idx: number) => ({
        id: idx.toString(),
        text: m.message,
        isUser: m.sender === 'user',
        timestamp: new Date(m.timestamp),
      }));

      // If empty session, provide default Oracle greeting
      if (formattedMessages.length === 0) {
        setMessages([
          {
            id: 'greeting',
            text: 'Greetings, Neo. I am the Oracle. I have been expecting you. The Matrix holds many secrets, and I am here to guide you through them. What questions do you bring to me today?',
            isUser: false,
            timestamp: new Date(),
          }
        ]);
      } else {
        setMessages(formattedMessages);
      }
      setView('chat');
    } catch (err) {
      console.error('Error loading session messages:', err);
      toast.error('Failed to load connection memory (messages).');
    }
  };

  const handleCreateSession = async () => {
    try {
      const response = await axios.post('http://localhost:8001/sessions', {
        user_id: user.id,
        name: `Neural Link ${Date.now().toString().slice(-4)}`
      });
      const newId = response.data.session_id;
      toast.success('New neural pathway open.');
      await fetchSessions();
      selectSession(newId);
    } catch (err) {
      console.error('Error creating session:', err);
      toast.error('Could not open new neural pathway.');
    }
  };

  const handleRenameSession = async () => {
    if (!currentSessionId || !renameText.trim()) return;
    try {
      await axios.put(`http://localhost:8001/sessions/${currentSessionId}`, {
        name: renameText.trim()
      });
      toast.success('Pathway re-labeled.');
      setIsRenaming(false);
      fetchSessions();
    } catch (err) {
      console.error('Error renaming session:', err);
      toast.error('Could not rename pathway.');
    }
  };

  const handleDeleteSession = async (sessionId: number) => {
    if (!confirm('Are you sure you want to terminate this neural connection?')) return;
    try {
      await axios.delete(`http://localhost:8001/sessions/${sessionId}`);
      toast.success('Connection terminated.');
      
      // If we deleted the active session, clear or pick another
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
        setMessages([]);
      }
      
      fetchSessions();
    } catch (err) {
      console.error('Error deleting session:', err);
      toast.error('Could not terminate connection.');
    }
  };

  const handleClearSession = async () => {
    if (!currentSessionId || !confirm('Wipe pathway memory buffer?')) return;
    try {
      await axios.post(`http://localhost:8001/sessions/${currentSessionId}/clear`);
      toast.success('Pathway memory wiped.');
      selectSession(currentSessionId);
    } catch (err) {
      console.error('Error clearing session messages:', err);
      toast.error('Memory wipe failed.');
    }
  };

  const handleSendMessage = async () => {
    if (!currentSessionId) {
      toast.error('No active session selected.');
      return;
    }
    if (!inputText.trim() && selectedFiles.length === 0) return;

    // Build files details to show locally if any
    const fileNames = selectedFiles.map(f => f.name);

    const userMsg: Message = {
      id: Date.now().toString(),
      text: inputText,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMsg]);
    const originalText = inputText;
    setInputText('');
    setIsLoading(true);

    try {
      // 1. Ingest files if uploaded
      if (selectedFiles.length > 0) {
        const formData = new FormData();
        formData.append('session_id', currentSessionId.toString());
        selectedFiles.forEach(file => {
          formData.append('files', file);
        });

        try {
          await axios.post('http://localhost:8001/ingest', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          });
          toast.success('Neural link uploaded documents compiled successfully.');
        } catch (fileError) {
          console.error('Error uploading files:', fileError);
          toast.error('Files failed to merge into session context.');
          setIsLoading(false);
          return;
        }
      }

      // Clear files
      setSelectedFiles([]);
      setShowFileUpload(false);

      // 2. Query Chat API
      const response = await axios.post('http://localhost:8001/chat', {
        session_id: currentSessionId,
        message: originalText,
        provider: provider.toLowerCase(),
        model_name: modelName,
      });

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: response.data.response,
        isUser: false,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      console.error('Error posting message:', err);
      toast.error('The Oracle failed to respond. Interface desynced.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSpeechTranscript = (transcript: string) => {
    setInputText(prev => (prev ? prev + ' ' + transcript : transcript));
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  // --- Profile Page Functions ---
  const loadProfile = async () => {
    try {
      const response = await axios.get(`http://localhost:8001/profile/${user.id}`);
      const data = response.data;
      setFullName(data.full_name || '');
      setDob(data.dob || '');
      setEmail(data.email || '');
      setProfilePicPath(data.profile_pic_path || '');
      setView('profile');
    } catch (err) {
      console.error('Error loading profile:', err);
      toast.error('Could not decrypt operator profile.');
    }
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword && newPassword !== confirmPassword) {
      toast.error('New passcode confirmations do not match.');
      return;
    }

    setIsProfileUpdating(true);
    try {
      await axios.put(`http://localhost:8001/profile/${user.id}`, {
        full_name: fullName,
        dob: dob,
        email: email,
        profile_pic_path: profilePicPath,
        password: newPassword || undefined
      });
      toast.success('Operator profile successfully updated.');
      setNewPassword('');
      setConfirmPassword('');
      setView('chat');
    } catch (err) {
      console.error('Error updating profile:', err);
      toast.error('Profile update write failed.');
    } finally {
      setIsProfileUpdating(false);
    }
  };

  return (
    <div className="flex h-screen max-h-screen matrix-terminal crt-monitor overflow-hidden text-primary">
      <div className="glitch-effect"></div>
      
      {/* Sidebar: Navigation, Connections, Settings */}
      <div className="w-80 border-r border-primary flex flex-col bg-black/90 z-10">
        {/* User Info Header */}
        <div className="p-4 border-b border-primary">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full border border-primary flex items-center justify-center bg-primary/10">
              <User className="w-5 h-5 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-sm font-bold font-mono truncate text-primary uppercase">
                {user.username}
              </h2>
              <p className="text-[10px] text-muted-foreground font-mono truncate uppercase">
                Operator ID: {user.id}
              </p>
            </div>
          </div>
          
          <div className="flex gap-2 mt-4">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={loadProfile}
              className="flex-1 font-mono text-xs border-primary text-primary hover:bg-primary/20 bg-transparent"
            >
              <Settings className="w-3.5 h-3.5 mr-1" /> PROFILE
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onLogout}
              className="font-mono text-xs border-destructive text-destructive hover:bg-destructive/20 bg-transparent"
            >
              <LogOut className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>

        {/* Model Core Decoder Selection */}
        <div className="p-4 border-b border-primary/40 space-y-3 bg-black/40">
          <span className="text-[10px] font-mono font-bold text-muted-foreground uppercase block tracking-wider">
            CORE DECODER CHANNEL
          </span>
          <div className="space-y-2">
            <div>
              <label className="text-[9px] font-mono text-primary/70 block mb-1 uppercase">PROVIDER</label>
              <select
                value={provider}
                onChange={(e) => {
                  const prov = e.target.value as 'Gemini' | 'NVIDIA' | 'Groq';
                  setProvider(prov);
                  if (prov === 'Gemini') setModelName('models/gemini-2.5-flash');
                  else if (prov === 'NVIDIA') setModelName('nvidia/llama-3.1-nemotron-nano-vl-8b-v1');
                  else setModelName('llama-3.3-70b-versatile');
                }}
                className="w-full bg-black border border-primary/50 text-primary font-mono text-[11px] p-1 rounded outline-none cursor-pointer focus:border-primary focus:ring-1 focus:ring-primary"
              >
                <option value="Gemini">GEMINI (GOOGLE)</option>
                <option value="NVIDIA">NVIDIA NIM</option>
                <option value="Groq">GROQ CORE</option>
              </select>
            </div>

            <div>
              <label className="text-[9px] font-mono text-primary/70 block mb-1 uppercase">MODEL ENGINE</label>
              <select
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                className="w-full bg-black border border-primary/50 text-primary font-mono text-[11px] p-1 rounded outline-none cursor-pointer focus:border-primary focus:ring-1 focus:ring-primary truncate"
              >
                {provider === 'Gemini' && (
                  <>
                    <option value="models/gemini-2.5-flash">gemini-2.5-flash (default)</option>
                    <option value="models/gemini-2.5-pro">gemini-2.5-pro (advanced)</option>
                  </>
                )}
                {provider === 'NVIDIA' && (
                  <>
                    <option value="nvidia/llama-3.1-nemotron-nano-vl-8b-v1">nemotron-nano-8b</option>
                    <option value="meta/llama-3.1-405b-instruct">llama-3.1-405b (large)</option>
                    <option value="nvidia/llama-3.1-nemotron-70b-instruct">nemotron-70b</option>
                  </>
                )}
                {provider === 'Groq' && (
                  <>
                    <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
                    <option value="llama-3.1-8b-instant">llama-3.1-8b-instant</option>
                    <option value="mixtral-8x7b-32768">mixtral-8x7b-32768</option>
                  </>
                )}
              </select>
            </div>
          </div>
        </div>

        {/* Connections List */}
        <div className="flex-1 flex flex-col min-h-0">
          <div className="p-3 flex justify-between items-center">
            <span className="text-xs font-mono font-bold text-muted-foreground uppercase">
              NEURAL LINKS
            </span>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={handleCreateSession}
              className="text-primary hover:bg-primary/20 p-1 h-auto"
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>

          <ScrollArea className="flex-1 p-2">
            <div className="space-y-1">
              {sessions.map((s) => (
                <div
                  key={s.id}
                  onClick={() => selectSession(s.id)}
                  className={`group flex items-center justify-between p-2.5 rounded font-mono text-xs cursor-pointer transition-all duration-200 ${
                    currentSessionId === s.id
                      ? 'bg-primary/20 border border-primary/50 text-primary'
                      : 'hover:bg-primary/10 text-muted-foreground hover:text-primary border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
                    <span className="truncate">{s.name || `Session ${s.id}`}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteSession(s.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 hover:bg-transparent text-destructive p-0 h-auto w-auto transition-opacity"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              ))}
              {sessions.length === 0 && (
                <div className="text-center py-6 text-xs text-muted-foreground font-mono">
                  No active channels.
                </div>
              )}
            </div>
          </ScrollArea>
        </div>
      </div>

      {/* Main Panel */}
      <div className="flex-1 flex gap-4 p-4 overflow-hidden relative z-10">
        
        {/* Chat / Profile Screen */}
        <div className="flex-1 flex flex-col min-w-0 bg-black/40 border border-primary rounded p-2">
          
          {view === 'profile' ? (
            /* PROFILE SCREEN */
            <div className="flex-1 flex flex-col p-4">
              <div className="flex items-center gap-2 mb-6 border-b border-primary/30 pb-3">
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => setView('chat')}
                  className="text-primary hover:bg-primary/20 p-1"
                >
                  <ArrowLeft className="w-5 h-5" />
                </Button>
                <h1 className="text-xl font-bold font-mono text-primary matrix-glow">
                  OPERATOR PROFILE CONFIGURATION
                </h1>
              </div>

              <form onSubmit={handleProfileUpdate} className="space-y-4 max-w-xl overflow-y-auto pr-2 scrollbar-matrix">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-mono text-primary">FULL LEGAL NAME</label>
                    <Input
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g. Thomas A. Anderson"
                      className="font-mono matrix-border bg-black border-primary text-primary"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-mono text-primary">DATE OF BIRTH</label>
                    <Input
                      value={dob}
                      onChange={(e) => setDob(e.target.value)}
                      placeholder="e.g. 1971-09-13"
                      className="font-mono matrix-border bg-black border-primary text-primary"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-mono text-primary">COMMUNICATION ADDRESS (EMAIL)</label>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="e.g. neophyte@realworld.org"
                    className="font-mono matrix-border bg-black border-primary text-primary"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-mono text-primary">NEURAL PROFILE PORTRAIT URL</label>
                  <Input
                    value={profilePicPath}
                    onChange={(e) => setProfilePicPath(e.target.value)}
                    placeholder="e.g. /avatars/neo.jpg"
                    className="font-mono matrix-border bg-black border-primary text-primary"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4 pt-2">
                  <div className="space-y-1">
                    <label className="text-xs font-mono text-primary">NEW ACCESS PASSCODE</label>
                    <Input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Leave blank to keep same"
                      className="font-mono matrix-border bg-black border-primary text-primary"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-mono text-primary">CONFIRM NEW PASSCODE</label>
                    <Input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Leave blank to keep same"
                      className="font-mono matrix-border bg-black border-primary text-primary"
                    />
                  </div>
                </div>

                <div className="pt-4 flex gap-2">
                  <Button
                    type="submit"
                    disabled={isProfileUpdating}
                    className="matrix-border bg-primary hover:bg-primary/85 text-black font-mono"
                  >
                    {isProfileUpdating ? 'SAVING CONFIG...' : 'WRITE PROFILE'}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setView('chat')}
                    className="matrix-border text-primary hover:bg-primary/10 bg-transparent border-primary font-mono"
                  >
                    CANCEL
                  </Button>
                </div>
              </form>
            </div>
          ) : (
            /* CHAT SCREEN */
            <div className="flex-1 flex flex-col min-h-0">
              
              {/* Active Session Header details */}
              {currentSessionId ? (
                <div className="flex items-center justify-between p-3 border-b border-primary/30">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {isRenaming ? (
                      <div className="flex items-center gap-1.5 w-full max-w-sm">
                        <Input
                          value={renameText}
                          onChange={(e) => setRenameText(e.target.value)}
                          className="font-mono matrix-border h-7 bg-black border-primary text-primary text-xs"
                          placeholder="Rename connection..."
                        />
                        <Button 
                          size="sm" 
                          onClick={handleRenameSession}
                          className="h-7 text-xs font-mono bg-primary text-black"
                        >
                          SAVE
                        </Button>
                        <Button 
                          size="sm" 
                          variant="ghost" 
                          onClick={() => setIsRenaming(false)}
                          className="h-7 px-2 hover:bg-primary/20 text-primary"
                        >
                          <X className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    ) : (
                      <>
                        <h1 className="text-base font-bold font-mono text-primary matrix-glow truncate">
                          {sessions.find(s => s.id === currentSessionId)?.name || `Session ${currentSessionId}`}
                        </h1>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => {
                            const name = sessions.find(s => s.id === currentSessionId)?.name || '';
                            setRenameText(name);
                            setIsRenaming(true);
                          }}
                          className="text-primary hover:bg-primary/20 p-1 h-auto"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </Button>
                      </>
                    )}
                  </div>

                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={handleClearSession}
                      className="font-mono text-xs border-primary text-primary hover:bg-primary/10 bg-transparent"
                    >
                      WIPE BUFFER
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="p-3 border-b border-primary/30">
                  <h1 className="text-base font-bold font-mono text-primary">
                    ORACLE NEURAL LINK
                  </h1>
                </div>
              )}

              {/* Chat messages viewport */}
              <ScrollArea 
                ref={scrollAreaRef}
                className="flex-1 p-4"
              >
                {currentSessionId ? (
                  messages.map((message, index) => (
                    <ChatMessage
                      key={message.id}
                      message={message.text}
                      isUser={message.isUser}
                      timestamp={message.timestamp}
                      isLastMessage={!message.isUser && index === messages.length - 1}
                    />
                  ))
                ) : (
                  <div className="flex h-full items-center justify-center text-center font-mono text-sm text-muted-foreground flex-col gap-2 p-8 py-20">
                    <MessageSquare className="w-8 h-8 text-primary animate-pulse" />
                    <p>WAKING UP FROM THE SIMULATION...</p>
                    <p className="text-xs">SELECT OR INITIALIZE A NEW NEURAL CHANNEL FROM THE SIDEBAR TO TALK TO THE ORACLE.</p>
                  </div>
                )}
                
                {isLoading && (
                  <div className="flex justify-start mb-4">
                    <Card className="p-3 matrix-terminal bg-card border-primary">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce matrix-glow"></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce matrix-glow" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce matrix-glow" style={{animationDelay: '0.2s'}}></div>
                      </div>
                    </Card>
                  </div>
                )}
              </ScrollArea>

              {/* File Upload viewport overlay */}
              {currentSessionId && showFileUpload && (
                <div className="p-4 border-t border-primary/30 bg-black/80">
                  <FileUpload
                    onFilesSelect={setSelectedFiles}
                    selectedFiles={selectedFiles}
                    onRemoveFile={handleRemoveFile}
                  />
                </div>
              )}

              {/* Input console */}
              {currentSessionId && (
                <div className="p-4 border-t border-primary/30">
                  <div className="flex gap-2 items-end">
                    <div className="flex-1">
                      <Input
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask the Oracle your question..."
                        className="font-mono matrix-border bg-black border-primary text-primary"
                        disabled={isLoading}
                      />
                    </div>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowFileUpload(!showFileUpload)}
                        className={`matrix-border hover:bg-primary/20 border-primary text-primary ${showFileUpload ? 'bg-primary/25' : 'bg-transparent'}`}
                      >
                        <Paperclip className="w-4 h-4" />
                      </Button>
                      <SpeechToText
                        onTranscript={handleSpeechTranscript}
                        disabled={isLoading}
                      />
                      <Button
                        onClick={handleSendMessage}
                        disabled={isLoading || (!inputText.trim() && selectedFiles.length === 0)}
                        className="matrix-border bg-primary text-black hover:bg-primary/80 font-bold"
                      >
                        <Send className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              )}

            </div>
          )}
        </div>

        {/* Text Editor panel on right */}
        {view === 'chat' && currentSessionId && (
          <div className="w-1/3 flex flex-col bg-black/40 border border-primary rounded p-2">
            <Tabs defaultValue="editor" className="flex-1 flex flex-col">
              <TabsList className="grid w-full grid-cols-3 matrix-border border-primary">
                <TabsTrigger value="editor" className="font-mono text-xs data-[state=active]:bg-primary/20 data-[state=active]:text-primary text-muted-foreground bg-transparent">Editor</TabsTrigger>
                <TabsTrigger value="output" className="font-mono text-xs data-[state=active]:bg-primary/20 data-[state=active]:text-primary text-muted-foreground bg-transparent">Output</TabsTrigger>
                <TabsTrigger value="graph" className="font-mono text-xs data-[state=active]:bg-primary/20 data-[state=active]:text-primary text-muted-foreground bg-transparent">Graph View</TabsTrigger>
              </TabsList>
              
              <TabsContent value="editor" className="flex-1 mt-2">
                <TextEditor
                  content={editorContent}
                  onChange={setEditorContent}
                />
              </TabsContent>
              
              <TabsContent value="output" className="flex-1 mt-2">
                <TextEditor
                  content={messages.filter(m => !m.isUser).slice(-1)[0]?.text || 'No Oracle transmission captured yet...'}
                  readOnly={true}
                />
              </TabsContent>

              <TabsContent value="graph" className="flex-1 mt-2 flex flex-col">
                <GraphView sessionId={currentSessionId} />
              </TabsContent>
            </Tabs>
          </div>
        )}

      </div>
    </div>
  );
};