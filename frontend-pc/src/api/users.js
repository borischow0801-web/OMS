import api from './index'

export const userApi = {
  // 获取用户列表
  getUsers: (params) => api.get('/accounts/users/', { params }),
  
  // 获取当前用户信息
  getCurrentUser: () => api.get('/accounts/users/me/'),
  
  // 创建用户
  createUser: (data) => api.post('/accounts/users/', data),
  
  // 更新用户
  updateUser: (id, data) => api.patch(`/accounts/users/${id}/`, data),
  
  // 修改密码
  changePassword: (data) => api.post('/accounts/users/change_password/', data),
  
  // 获取员工列表
  getEmployees: () => api.get('/accounts/users/employees/'),
}

