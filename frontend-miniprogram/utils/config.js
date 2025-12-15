// API配置
const config = {
  // 开发环境
  dev: {
    apiBaseUrl: 'http://localhost:8000/api',
  },
  // 生产环境
  prod: {
    apiBaseUrl: 'https://your-domain.com/api',
  },
}

// 根据环境选择配置
const env = 'dev' // 开发时使用 dev，生产时改为 prod
const currentConfig = config[env]

module.exports = {
  apiBaseUrl: currentConfig.apiBaseUrl,
}

