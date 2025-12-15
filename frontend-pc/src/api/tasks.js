import api from './index'

export const taskApi = {
  // 获取任务列表
  getTasks: (params) => api.get('/tasks/tasks/', { params }),
  
  // 获取任务详情
  getTask: (id) => api.get(`/tasks/tasks/${id}/`),
  
  // 创建任务
  createTask: (data) => api.post('/tasks/tasks/', data),
  
  // 更新任务
  updateTask: (id, data) => api.patch(`/tasks/tasks/${id}/`, data),
  
  // 审核任务
  reviewTask: (id, data) => api.post(`/tasks/tasks/${id}/review/`, data),
  
  // 指派任务
  assignTask: (id, data) => api.post(`/tasks/tasks/${id}/assign/`, data),
  
  // 处理任务
  handleTask: (id, data) => api.post(`/tasks/tasks/${id}/handle/`, data),
  
  // 完成任务
  completeTask: (id, data) => api.post(`/tasks/tasks/${id}/complete/`, data),
  
  // 确认任务
  confirmTask: (id, data) => api.post(`/tasks/tasks/${id}/confirm/`, data),
  
  // 添加评论
  addComment: (id, data) => api.post(`/tasks/tasks/${id}/add_comment/`, data),
  
  // 设置协助员工
  setAssistants: (id, data) => api.post(`/tasks/tasks/${id}/set_assistants/`, data),
  
  // 上传附件
  uploadAttachment: (id, file) => {
    const formData = new FormData()
    formData.append('file', file)
    // axios会自动检测FormData并设置正确的Content-Type和boundary
    return api.post(`/tasks/tasks/${id}/upload_attachment/`, formData)
  },
  
  // 删除附件
  deleteAttachment: (id, attachmentId) => api.delete(`/tasks/tasks/${id}/attachments/${attachmentId}/`),
  
  // 下载附件
  downloadAttachment: (id, attachmentId) => api.get(`/tasks/tasks/${id}/attachments/${attachmentId}/download/`, {
    responseType: 'blob',
  }),
  
  // 提交草稿
  submitDraft: (id) => api.post(`/tasks/tasks/${id}/submit_draft/`),
}

