import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { TabBar } from 'antd-mobile';
import { AppOutline, PicturesOutline } from 'antd-mobile-icons';

// 底部导航配置
const tabs = [
  {
    key: '/home',
    title: '视觉识别',
    icon: <AppOutline />,
  },
  {
    key: '/baidu',
    title: '百度云API',
    icon: <PicturesOutline />,
  },
];

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleTabChange = (key: string) => {
    navigate(key);
  };

  return (
    <div className="flex h-full w-full flex-col">
      {/* 主内容区 */}
      <div className="flex-1 overflow-hidden">
        <Outlet />
      </div>

      {/* 底部导航栏 */}
      <TabBar
        activeKey={location.pathname}
        onChange={handleTabChange}
        className="border-t bg-white shadow-[0_-2px_10px_rgba(0,0,0,0.05)]"
      >
        {tabs.map((item) => (
          <TabBar.Item
            key={item.key}
            icon={item.icon}
            title={item.title}
          />
        ))}
      </TabBar>
    </div>
  );
};

export default Layout;
