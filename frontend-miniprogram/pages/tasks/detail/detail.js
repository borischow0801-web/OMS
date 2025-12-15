// pages/tasks/detail/detail.js
Page({
  data: {
    task: null,
    loading: false,
  },

  onLoad(options) {
    if (options.id) {
      this.loadTask(options.id)
    }
  },

  async loadTask(id) {
    this.setData({ loading: true })
    try {
      const config = require('../../../utils/config')
      const token = wx.getStorageSync('token')
      const response = await wx.request({
        url: `${config.apiBaseUrl}/tasks/tasks/${id}/`,
        method: 'GET',
        header: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (response.statusCode === 200) {
        this.setData({
          task: response.data,
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

  // 拍照上传附件（预留功能，待后续验证）
  async takePhotoAndUpload() {
    const taskId = this.data.task?.id
    if (!taskId) {
      wx.showToast({
        title: '任务不存在',
        icon: 'none',
      })
      return
    }

    try {
      // 选择图片（支持拍照或从相册选择）
      const res = await wx.chooseImage({
        count: 1, // 一次只能选择一张
        sourceType: ['camera', 'album'], // 可以拍照或从相册选择
      })

      if (res.tempFilePaths && res.tempFilePaths.length > 0) {
        const tempFilePath = res.tempFilePaths[0]
        
        wx.showLoading({
          title: '上传中...',
        })

        const config = require('../../../utils/config')
        const token = wx.getStorageSync('token')
        
        // 上传文件到服务器
        const uploadRes = await wx.uploadFile({
          url: `${config.apiBaseUrl}/tasks/tasks/${taskId}/upload_attachment/`,
          filePath: tempFilePath,
          name: 'file',
          header: {
            Authorization: `Bearer ${token}`,
          },
        })

        wx.hideLoading()

        if (uploadRes.statusCode === 200 || uploadRes.statusCode === 201) {
          wx.showToast({
            title: '上传成功',
            icon: 'success',
          })
          // 重新加载任务详情
          this.loadTask(taskId)
        } else {
          const errorData = JSON.parse(uploadRes.data || '{}')
          wx.showToast({
            title: errorData.error || '上传失败',
            icon: 'none',
          })
        }
      }
    } catch (error) {
      wx.hideLoading()
      wx.showToast({
        title: '上传失败',
        icon: 'none',
      })
      console.error('拍照上传失败:', error)
    }
  },

  // 下载附件（预留功能）
  async downloadAttachment(e) {
    const attachmentId = e.currentTarget.dataset.id
    const taskId = this.data.task?.id
    if (!taskId || !attachmentId) {
      wx.showToast({
        title: '参数错误',
        icon: 'none',
      })
      return
    }

    try {
      wx.showLoading({
        title: '下载中...',
      })

      const config = require('../../../utils/config')
      const token = wx.getStorageSync('token')
      
      const response = await wx.request({
        url: `${config.apiBaseUrl}/tasks/tasks/${taskId}/attachments/${attachmentId}/download/`,
        method: 'GET',
        header: {
          Authorization: `Bearer ${token}`,
        },
        responseType: 'arraybuffer',
      })

      wx.hideLoading()

      if (response.statusCode === 200) {
        // 保存文件到本地
        const fs = wx.getFileSystemManager()
        const attachment = this.data.task.attachments.find(a => a.id === attachmentId)
        const filename = attachment?.original_filename || 'attachment'
        const filePath = `${wx.env.USER_DATA_PATH}/${filename}`
        
        fs.writeFileSync(filePath, response.data)
        
        wx.showToast({
          title: '下载成功',
          icon: 'success',
        })
      } else {
        wx.showToast({
          title: '下载失败',
          icon: 'none',
        })
      }
    } catch (error) {
      wx.hideLoading()
      wx.showToast({
        title: '下载失败',
        icon: 'none',
      })
      console.error('下载附件失败:', error)
    }
  },
})

