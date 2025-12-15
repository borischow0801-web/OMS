import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../api'

const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (username, password) => {
        try {
          const response = await api.post('/auth/login/', { username, password })
          const { access, refresh, ...userData } = response.data
          
          set({
            user: userData,
            token: access,
            refreshToken: refresh,
            isAuthenticated: true,
          })
          
          // 设置axios默认header
          api.defaults.headers.common['Authorization'] = `Bearer ${access}`
          
          return { success: true }
        } catch (error) {
          return {
            success: false,
            error: error.response?.data?.detail || '登录失败',
          }
        }
      },

      logout: () => {
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
        })
        delete api.defaults.headers.common['Authorization']
        // 清除持久化存储
        localStorage.removeItem('auth-storage')
      },

      setUser: (user) => set({ user }),
      setToken: (token) => {
        set({ token })
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

// 初始化时设置token
const token = useAuthStore.getState().token
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

export { useAuthStore }

