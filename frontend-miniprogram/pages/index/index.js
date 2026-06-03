// pages/index/index.js
Page({
  data: {
    userInfo: null,
    stats: {
      total: 0,
      pending: 0,
      completed: 0,
    },
  },

  onLoad() {
    this.checkLogin()
    this.loadStats()
  },

  onShow() {
    this.loadStats()
  },

  checkLogin() {
    const app = getApp()
    if (app.globalData.userInfo) {
      this.setData({
        userInfo: app.globalData.userInfo,
      })
    } else {
      wx.redirectTo({
        url: '/pages/login/login',
      })
    }
  },

  loadStats() {
    // TODO: 调用API加载统计数据
    console.log('加载统计数据')
  },

  navigateToTasks() {
    wx.switchTab({
      url: '/pages/tasks/list/list',
    })
  },
})

