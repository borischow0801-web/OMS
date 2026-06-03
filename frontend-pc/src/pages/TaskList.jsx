import { Table, Button, Tag, Space, Input, Select, DatePicker } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { taskApi } from '../api/tasks'
import { formatDateTime, getUserDisplayName } from '../utils/format'
import { useAuthStore } from '../store/authStore'
import dayjs from 'dayjs'

const { Search } = Input
const { Option } = Select

function TaskList() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { user } = useAuthStore()
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(false)
  
  // 从URL参数初始化状态
  const getFiltersFromParams = () => {
    return {
      status: searchParams.get('status') || '',
      task_type: searchParams.get('task_type') || '',
      title: searchParams.get('title') || '',
      priority: searchParams.get('priority') || '',
      created_date: searchParams.get('created_date') || '',
    }
  }
  
  const getPaginationFromParams = () => {
    return {
      current: parseInt(searchParams.get('page') || '1', 10),
      pageSize: parseInt(searchParams.get('page_size') || '10', 10),
      total: 0,
    }
  }
  
  const [pagination, setPagination] = useState(() => getPaginationFromParams())
  const [filters, setFilters] = useState(() => getFiltersFromParams())
  
  // 只有使用方和管理员可以创建任务
  const canCreateTask = user?.role === 'user' || user?.role === 'admin'

  // 当URL参数变化时，更新状态（从详情页返回时）
  useEffect(() => {
    const urlFilters = getFiltersFromParams()
    const urlPagination = getPaginationFromParams()
    
    // 检查是否有变化，避免无限循环
    const filtersChanged = JSON.stringify(filters) !== JSON.stringify(urlFilters)
    const paginationChanged = pagination.current !== urlPagination.current || pagination.pageSize !== urlPagination.pageSize
    
    if (filtersChanged) {
      setFilters(urlFilters)
    }
    if (paginationChanged) {
      setPagination(prev => ({
        ...prev,
        current: urlPagination.current,
        pageSize: urlPagination.pageSize,
      }))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  // 更新URL参数（当filters或pagination变化时）
  useEffect(() => {
    const params = new URLSearchParams()
    // 添加过滤条件
    Object.keys(filters).forEach(key => {
      if (filters[key]) {
        params.set(key, filters[key])
      }
    })
    // 添加分页参数
    if (pagination.current > 1) {
      params.set('page', pagination.current.toString())
    }
    if (pagination.pageSize !== 10) {
      params.set('page_size', pagination.pageSize.toString())
    }
    // 只有当URL参数与当前状态不同时才更新，避免循环
    const currentParams = new URLSearchParams(searchParams)
    if (params.toString() !== currentParams.toString()) {
      setSearchParams(params, { replace: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, pagination.current, pagination.pageSize])

  useEffect(() => {
    loadTasks()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, pagination.current, pagination.pageSize])

  const loadTasks = async () => {
    setLoading(true)
    try {
      // 构建查询参数
      const params = {
        ...filters,
        page: pagination.current,
        page_size: pagination.pageSize,
      }
      // 移除空值
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null || params[key] === undefined) {
          delete params[key]
        }
      })
      
      const response = await taskApi.getTasks(params)
      // 处理分页响应
      if (response.data.results) {
        setTasks(response.data.results)
        setPagination(prev => ({
          ...prev,
          total: response.data.count || 0,
        }))
      } else {
        setTasks(response.data)
        setPagination(prev => ({
          ...prev,
          total: response.data.length || 0,
        }))
      }
    } catch (error) {
      console.error('加载任务失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTableChange = (newPagination) => {
    setPagination(prev => ({
      ...prev,
      current: newPagination.current,
      pageSize: newPagination.pageSize,
    }))
  }

  const getStatusTag = (status) => {
    const statusMap = {
      draft: { color: 'default', text: '草稿' },
      pending_review: { color: 'orange', text: '待审核' },
      reviewed: { color: 'blue', text: '已审核' },
      assigned: { color: 'cyan', text: '已指派' },
      in_progress: { color: 'processing', text: '处理中' },
      completed: { color: 'purple', text: '已完成' },
      confirmed: { color: 'success', text: '已确认' },
      closed: { color: 'default', text: '已结单' },
    }
    const statusInfo = statusMap[status] || { color: 'default', text: status }
    return <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
  }

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'task_type_display',
      key: 'task_type',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) => getStatusTag(status),
    },
    {
      title: '优先级',
      dataIndex: 'priority_display',
      key: 'priority',
      width: 100,
    },
    {
      title: '创建人',
      dataIndex: ['creator'],
      key: 'creator',
      width: 120,
      render: (creator) => getUserDisplayName(creator),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time) => formatDateTime(time),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button 
          type="link" 
          onClick={() => {
            // 保存当前查询参数到location state
            const currentParams = new URLSearchParams(searchParams)
            navigate(`/tasks/${record.id}`, { 
              state: { 
                returnUrl: `/tasks?${currentParams.toString()}` 
              } 
            })
          }}
        >
          查看
        </Button>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
        <Space wrap size="middle">
          <Space direction="vertical" size="small" style={{ marginBottom: 0 }}>
            <span style={{ fontSize: 12, color: '#666' }}>任务类型</span>
            <Select
              style={{ width: 120 }}
              placeholder="请选择"
              allowClear
              value={filters.task_type}
              onChange={(value) => {
                const newFilters = { ...filters, task_type: value || '' }
                setFilters(newFilters)
                setPagination(prev => ({ ...prev, current: 1 }))
              }}
            >
              <Option value="problem">问题</Option>
              <Option value="requirement">需求</Option>
            </Select>
          </Space>
          <Space direction="vertical" size="small" style={{ marginBottom: 0 }}>
            <span style={{ fontSize: 12, color: '#666' }}>任务状态</span>
            <Select
              style={{ width: 120 }}
              placeholder="请选择"
              allowClear
              value={filters.status}
              onChange={(value) => {
                const newFilters = { ...filters, status: value || '' }
                setFilters(newFilters)
                setPagination(prev => ({ ...prev, current: 1 }))
              }}
            >
              <Option value="draft">草稿</Option>
              <Option value="pending_review">待审核</Option>
              <Option value="reviewed">已审核</Option>
              <Option value="assigned">已指派</Option>
              <Option value="in_progress">处理中</Option>
              <Option value="completed">已完成</Option>
              <Option value="confirmed">已确认</Option>
              <Option value="closed">已结单</Option>
            </Select>
          </Space>
          <Space direction="vertical" size="small" style={{ marginBottom: 0 }}>
            <span style={{ fontSize: 12, color: '#666' }}>优先级</span>
            <Select
              style={{ width: 120 }}
              placeholder="请选择"
              allowClear
              value={filters.priority}
              onChange={(value) => {
                const newFilters = { ...filters, priority: value || '' }
                setFilters(newFilters)
                setPagination(prev => ({ ...prev, current: 1 }))
              }}
            >
              <Option value="low">低</Option>
              <Option value="medium">中</Option>
              <Option value="high">高</Option>
              <Option value="urgent">紧急</Option>
            </Select>
          </Space>
          <Space direction="vertical" size="small" style={{ marginBottom: 0 }}>
            <span style={{ fontSize: 12, color: '#666' }}>创建日期</span>
            <DatePicker
              style={{ width: 180 }}
              placeholder="请选择日期"
              allowClear
              value={filters.created_date ? dayjs(filters.created_date) : null}
              onChange={(date) => {
                const newFilters = { ...filters, created_date: date ? date.format('YYYY-MM-DD') : '' }
                setFilters(newFilters)
                setPagination(prev => ({ ...prev, current: 1 }))
              }}
            />
          </Space>
          <Space direction="vertical" size="small" style={{ marginBottom: 0 }}>
            <span style={{ fontSize: 12, color: '#666' }}>标题关键字</span>
            <Space.Compact style={{ width: 200 }}>
              <Input
                placeholder="请输入标题关键字"
                allowClear
                value={filters.title}
                onChange={(e) => {
                  const newFilters = { ...filters, title: e.target.value }
                  setFilters(newFilters)
                }}
                onPressEnter={(e) => {
                  const value = e.target.value
                  const newFilters = { ...filters, title: value }
                  setFilters(newFilters)
                  setPagination(prev => ({ ...prev, current: 1 }))
                }}
              />
              <Button 
                type="primary"
                onClick={() => {
                  const newFilters = { ...filters, title: filters.title }
                  setFilters(newFilters)
                  setPagination(prev => ({ ...prev, current: 1 }))
                }}
              >
                搜索
              </Button>
            </Space.Compact>
          </Space>
        </Space>
        {canCreateTask && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/tasks/create')}>
            创建任务
          </Button>
        )}
      </div>
      <Table
        columns={columns}
        dataSource={tasks}
        rowKey="id"
        loading={loading}
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          pageSizeOptions: ['10', '20', '50', '100'],
        }}
        onChange={handleTableChange}
      />
    </div>
  )
}

export default TaskList

