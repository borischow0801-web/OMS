import api from './index'

export const maintenanceApi = {
  // 获取运维记录列表
  getRecords: (params) => {
    return api.get('/maintenance/records/', { params })
  },
  
  // 获取单个运维记录
  getRecord: (id) => {
    return api.get(`/maintenance/records/${id}/`)
  },
  
  // 创建运维记录
  createRecord: (data) => {
    return api.post('/maintenance/records/', data)
  },
  
  // 更新运维记录
  updateRecord: (id, data) => {
    return api.patch(`/maintenance/records/${id}/`, data)
  },
  
  // 删除运维记录
  deleteRecord: (id) => {
    return api.delete(`/maintenance/records/${id}/`)
  },
  
  // 获取统计报告
  getStatistics: () => {
    return api.get('/maintenance/records/statistics/')
  },

  // 上传附件
  uploadAttachment: (recordId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/maintenance/records/${recordId}/upload_attachment/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // 删除附件
  deleteAttachment: (recordId, attachmentId) => {
    return api.delete(`/maintenance/records/${recordId}/attachments/${attachmentId}/`)
  },

  // 下载附件（返回 blob）
  downloadAttachment: (recordId, attachmentId) => {
    return api.get(`/maintenance/records/${recordId}/attachments/${attachmentId}/download/`, {
      responseType: 'blob',
    })
  },
}
