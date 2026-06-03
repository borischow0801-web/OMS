import dayjs from 'dayjs'

/**
 * 格式化日期时间
 * @param {string|Date} date - 日期字符串或Date对象
 * @returns {string} 格式化后的日期时间字符串，格式：YYYY-MM-DD HH:mm:ss
 */
export const formatDateTime = (date) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

/**
 * 获取用户显示名称
 * @param {object} user - 用户对象
 * @returns {string} 用户显示名称（优先显示full_name，其次username）
 */
export const getUserDisplayName = (user) => {
  if (!user) return '-'
  return user.full_name || user.username || '-'
}

