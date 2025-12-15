// pages/tasks/list/list.js
Page({
  data: {
    tasks: [],
    loading: false,
    status: '',
  },

  onLoad() {
    this.loadTasks()
  },

  onShow() {
    this.loadTasks()
  },

  async loadTasks() {
    this.setData({ loading: true })
    try {
      const config = require('../../../utils/config')
      const token = wx.getStorageSync('token')
      const response = await wx.request({
        url: `${config.apiBaseUrl}/tasks/tasks/`,
        method: 'GET',
        header: {
          Authorization: `Bearer ${token}`,
        },
        data: {
          status: this.data.status || undefined,
        },
      })

      if (response.statusCode === 200) {
        this.setData({
          tasks: response.data.results || response.data,
          loading: false,
        })
      } else {
        throw new Error('加载失败')
      }
    } catch (error) {
      this.setData({ loading: false })
      wx.showToast({
        title: '加载失败',
        icon: 'none',
      })
    }
  },

  navigateToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/tasks/detail/detail?id=${id}`,
    })
  },
})

