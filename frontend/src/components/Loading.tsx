import { Loader2 } from 'lucide-react';

interface LoadingProps {
  message?: string;
}

const Loading = ({ message = '正在处理中...' }: LoadingProps) => {
  return (
    <div className="loading-overlay">
      <div className="flex flex-col items-center gap-3">
        <Loader2 className="h-10 w-10 animate-spin text-primary-500" />
        <p className="text-sm font-medium text-gray-600">{message}</p>
      </div>
    </div>
  );
};

export default Loading;
