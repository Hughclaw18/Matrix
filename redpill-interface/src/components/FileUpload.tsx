import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Upload, X, File, Image, Video, FileText } from 'lucide-react';
import { toast } from 'sonner';

interface FileUploadProps {
  onFilesSelect: (files: File[]) => void;
  selectedFiles: File[];
  onRemoveFile: (index: number) => void;
}

export const FileUpload = ({ onFilesSelect, selectedFiles, onRemoveFile }: FileUploadProps) => {
  const [isDragActive, setIsDragActive] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFilesSelect([...selectedFiles, ...acceptedFiles]);
      toast.success(`${acceptedFiles.length} file(s) uploaded successfully`);
    }
    setIsDragActive(false);
  }, [onFilesSelect, selectedFiles]);

  const { getRootProps, getInputProps, isDragReject } = useDropzone({
    onDrop,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
      'video/*': ['.mp4', '.webm', '.ogg'],
      'audio/*': ['.mp3', '.wav', '.ogg'],
      'application/pdf': ['.pdf'],
      'text/*': ['.txt', '.md'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return <Image className="w-4 h-4" />;
    if (file.type.startsWith('video/')) return <Video className="w-4 h-4" />;
    if (file.type === 'application/pdf' || file.type.startsWith('text/')) return <FileText className="w-4 h-4" />;
    return <File className="w-4 h-4" />;
  };

  return (
    <div className="space-y-3">
      <Card
        {...getRootProps()}
        className={`p-6 border-2 border-dashed cursor-pointer transition-all duration-200 matrix-terminal
          ${isDragActive ? 'border-primary matrix-glow' : 'border-border'}
          ${isDragReject ? 'border-destructive' : ''}
        `}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-2 text-center">
          <Upload className="w-8 h-8 text-primary matrix-glow" />
          <div className="font-mono">
            <p className="text-sm text-foreground matrix-glow">
              {isDragActive ? 'Drop files here...' : 'Drag & drop files here'}
            </p>
            <p className="text-xs text-muted-foreground">
              or click to select files
            </p>
          </div>
          <p className="text-xs text-muted-foreground">
            Supports images, videos, documents (max 10MB)
          </p>
        </div>
      </Card>

      {selectedFiles.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-mono text-primary matrix-glow">
            Selected Files ({selectedFiles.length})
          </p>
          {selectedFiles.map((file, index) => (
            <Card key={index} className="p-3 matrix-terminal">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getFileIcon(file)}
                  <div className="font-mono">
                    <p className="text-sm text-foreground matrix-glow">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onRemoveFile(index)}
                  className="text-destructive hover:text-destructive-foreground hover:bg-destructive"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};