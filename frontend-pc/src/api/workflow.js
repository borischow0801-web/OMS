import api from './index'

export const workflowApi = {
  // 获取工作流日志
  getWorkflowLogs: (params) => api.get('/workflow/logs/', { params }),
  
  // 获取通知列表
  getNotifications: () => api.get('/workflow/notifications/'),
  
  // 标记通知已读
  markNotificationRead: (id) => api.post(`/workflow/notifications/${id}/mark_read/`),
  
  // 标记所有通知已读
  markAllNotificationsRead: () => api.post('/workflow/notifications/mark_all_read/'),
}

