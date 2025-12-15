import { Layout as AntLayout, Menu, Avatar, Dropdown, Badge, Button, message, Empty } from 'antd'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  FileTextOutlined,
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
  CheckOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../store/authStore'
import { useState, useEffect } from 'react'
import { workflowApi } from '../api/workflow'
import { formatDateTime } from '../utils/format'

const { Header, Sider, Content } = AntLayout

function Layout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    loadNotifications()
    const interval = setInterval(loadNotifications, 30000) // 每30秒刷新一次
    return () => clearInterval(interval)
  }, [])

  const loadNotifications = async () => {
    try {
      const response = await workflowApi.getNotifications()
      setNotifications(response.data.results || response.data)
      setUnreadCount(response.data.results?.filter(n => !n.is_read).length || 0)
    } catch (error) {
      console.error('加载通知失败:', error)
    }
  }

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '首页',
    },
    {
      key: '/tasks',
      icon: <FileTextOutlined />,
      label: '任务管理',
    },
  ]

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
    },
    {
      type: 'divider',
    },
    {
      key: 'userinfo',
      label: (
        <div style={{ padding: '4px 0', color: '#666', fontSize: '12px' }}>
          {user?.full_name || user?.username || '用户'}
          {user?.role_display && <div style={{ color: '#999' }}>{user.role_display}</div>}
        </div>
      ),
      disabled: true,
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ]

  const handleMenuClick = ({ key }) => {
    if (key === 'logout') {
      logout()
      navigate('/login')
    } else if (key === 'profile') {
      navigate('/profile')
    } else {
      navigate(key)
    }
  }

  const handleNotificationClick = async (notif) => {
    if (!notif.is_read) {
      try {
        await workflowApi.markNotificationRead(notif.id)
        loadNotifications()
      } catch (error) {
        console.error('标记已读失败:', error)
      }
    }
    if (notif.task) {
      navigate(`/tasks/${notif.task.id}`)
    }
  }

  const handleMarkAllRead = async () => {
    try {
      await workflowApi.markAllNotificationsRead()
      message.success('已标记所有通知为已读')
      loadNotifications()
    } catch (error) {
      message.error('批量标记已读失败')
      console.error('批量标记已读失败:', error)
    }
  }

  // 获取未读通知列表
  const unreadNotifications = notifications.filter(n => !n.is_read)
  
  // 通知下拉菜单内容
  const notificationDropdownContent = (
    <div style={{ width: 360, maxHeight: 500, backgroundColor: '#fff', borderRadius: 4, boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}>
      <div style={{ 
        padding: '12px 16px', 
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#fff',
        borderRadius: '4px 4px 0 0'
      }}>
        <div style={{ fontWeight: 'bold', fontSize: 14 }}>
          待办任务 {unreadCount > 0 && `(${unreadCount})`}
        </div>
        {unreadCount > 0 && (
          <Button 
            type="link" 
            size="small" 
            icon={<CheckOutlined />}
            onClick={handleMarkAllRead}
          >
            全部已读
          </Button>
        )}
      </div>
      <div style={{ 
        maxHeight: 400, 
        overflowY: 'auto',
        overflowX: 'hidden',
        backgroundColor: '#fff',
        borderRadius: '0 0 4px 4px'
      }}>
        {unreadNotifications.length === 0 ? (
          <Empty 
            description="暂无未读通知" 
            style={{ padding: '40px 0' }}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          unreadNotifications.map((notif) => (
            <div
              key={notif.id}
              onClick={() => handleNotificationClick(notif)}
              style={{
                padding: '12px 16px',
                borderBottom: '1px solid #f0f0f0',
                cursor: 'pointer',
                backgroundColor: '#f6ffed',
                transition: 'background-color 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#e6f7ff'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#f6ffed'
              }}
            >
              <div style={{ 
                fontWeight: 'bold',
                fontSize: 14,
                color: '#262626',
                marginBottom: 4
              }}>
                {notif.title}
              </div>
              <div style={{ 
                fontSize: 12, 
                color: '#999', 
                marginBottom: 4,
                lineHeight: '1.5'
              }}>
                {notif.content}
              </div>
              <div style={{ 
                fontSize: 11, 
                color: '#bfbfbf'
              }}>
                {formatDateTime(notif.created_at)}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider width={200} theme="light">
        <div style={{ padding: '16px', textAlign: 'center', fontWeight: 'bold' }}>
          运维管理系统
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ height: 'calc(100vh - 64px)', borderRight: 0 }}
        />
      </Sider>
      <AntLayout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: 18, fontWeight: 'bold' }}>
            {menuItems.find(item => item.key === location.pathname)?.label || '首页'}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <Dropdown
              popupRender={() => notificationDropdownContent}
              placement="bottomRight"
              trigger={['click']}
            >
              <Badge count={unreadCount}>
                <BellOutlined style={{ fontSize: 20, cursor: 'pointer' }} />
              </Badge>
            </Dropdown>
            <Dropdown
              menu={{ 
                items: userMenuItems,
                onClick: handleMenuClick
              }}
              placement="bottomRight"
            >
              <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Avatar icon={<UserOutlined />} />
                <span>{user?.full_name || user?.username || '用户'}</span>
              </div>
            </Dropdown>
          </div>
        </Header>
        <Content style={{ margin: '24px', background: '#fff', padding: '24px', minHeight: 280 }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  )
}

export default Layout

