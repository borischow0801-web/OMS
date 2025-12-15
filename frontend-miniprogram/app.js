// app.js
App({
  onLaunch() {
    // 小程序启动时执行
    console.log('小程序启动')
    
    // 检查登录状态
    const token = wx.getStorageSync('token')
    if (token) {
      // 验证token有效性
      this.checkToken(token)
    }
  },

  onShow() {
    // 小程序显示时执行
  },

  onHide() {
    // 小程序隐藏时执行
  },

  checkToken(token) {
    // TODO: 实现token验证逻辑
    console.log('检查token:', token)
  },

  globalData: {
    userInfo: null,
    token: null,
  },
})

