// pages/login/login.js
Page({
  data: {
    username: '',
    password: '',
  },

  onLoad() {
    // 检查是否已登录
    const token = wx.getStorageSync('token')
    if (token) {
      wx.switchTab({
        url: '/pages/index/index',
      })
    }
  },

  onUsernameInput(e) {
    this.setData({
      username: e.detail.value,
    })
  },

  onPasswordInput(e) {
    this.setData({
      password: e.detail.value,
    })
  },

  async handleLogin() {
    const { username, password } = this.data
    if (!username || !password) {
      wx.showToast({
        title: '请输入用户名和密码',
        icon: 'none',
      })
      return
    }

    wx.showLoading({
      title: '登录中...',
    })

    try {
      const config = require('../../utils/config')
      const response = await wx.request({
        url: `${config.apiBaseUrl}/auth/login/`,
        method: 'POST',
        data: { username, password },
      })

      if (response.statusCode === 200) {
        const { access, refresh } = response.data
        wx.setStorageSync('token', access)
        wx.setStorageSync('refreshToken', refresh)
        
        const app = getApp()
        app.globalData.token = access
        app.globalData.userInfo = response.data

        wx.hideLoading()
        wx.showToast({
          title: '登录成功',
          icon: 'success',
        })

        setTimeout(() => {
          wx.switchTab({
            url: '/pages/index/index',
          })
        }, 1500)
      } else {
        throw new Error(response.data.detail || '登录失败')
      }
    } catch (error) {
      wx.hideLoading()
      wx.showToast({
        title: error.message || '登录失败',
        icon: 'none',
      })
    }
  },
})

