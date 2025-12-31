import { useState } from 'react';
import { HomePage, BaiduApiPage } from './pages';

type PageType = 'home' | 'baidu-api';

const App = () => {
  const [currentPage, setCurrentPage] = useState<PageType>('home');

  return (
    <div className="flex h-full w-full flex-col">
      {/* 主内容区 */}
      <div className="flex-1 overflow-hidden">
        {currentPage === 'home' && <HomePage />}
        {currentPage === 'baidu-api' && <BaiduApiPage />}
      </div>

      {/* 底部导航栏 */}
      <nav className="flex items-center justify-around border-t bg-white py-2 shadow-[0_-2px_10px_rgba(0,0,0,0.05)]">
        <button
          onClick={() => setCurrentPage('home')}
          className={`flex flex-col items-center gap-1 px-4 py-1 ${
            currentPage === 'home' ? 'text-amber-500' : 'text-gray-400'
          }`}
          aria-label="视觉识别"
          tabIndex={0}
        >
          <span className="text-xl">⚡</span>
          <span className="text-xs">视觉识别</span>
        </button>
        <button
          onClick={() => setCurrentPage('baidu-api')}
          className={`flex flex-col items-center gap-1 px-4 py-1 ${
            currentPage === 'baidu-api' ? 'text-red-500' : 'text-gray-400'
          }`}
          aria-label="百度云API"
          tabIndex={0}
        >
          <span className="text-xl">🔴</span>
          <span className="text-xs">百度云API</span>
        </button>
      </nav>
    </div>
  );
};

export default App;
