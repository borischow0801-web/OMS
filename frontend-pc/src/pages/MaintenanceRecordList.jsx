import { Table, Button, Tag, Space, Input, Select, DatePicker, Popconfirm, message } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { maintenanceApi } from '../api/maintenance'
import { userApi } from '../api/users'
import { formatDateTime, getUserDisplayName } from '../utils/format'
import { useAuthStore } from '../store/authStore'
import dayjs from 'dayjs'

const { Search } = Input
const { Option } = Select
const { RangePicker } = DatePicker

function MaintenanceRecordList() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { user } = useAuthStore()
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(false)
  const [contractors, setContractors] = useState([])
  const [loadingContractors, setLoadingContractors] = useState(false)
  
  // 从URL参数初始化状态
  const getFiltersFromParams = () => {
    return {
      search: searchParams.get('search') || '',
      region: searchParams.get('region') || '',
      issue_type: searchParams.get('issue_type') || '',
      completion_status: searchParams.get('completion_status') || '',
      priority: searchParams.get('priority') || '',
      handler: searchParams.get('handler') || '',
      start_date: searchParams.get('start_date') || '',
      end_date: searchParams.get('end_date') || '',
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
  
  // 只有承建方可以访问
  const canAccess = user?.role === 'manager' || user?.role === 'employee'

  useEffect(() => {
    if (!canAccess) {
      message.error('您没有权限访问运维记录')
      navigate('/')
      return
    }
    loadContractors()
    loadRecords()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, pagination.current, pagination.pageSize])

  const loadContractors = async () => {
    if (contractors.length > 0) return // 已加载过
    setLoadingContractors(true)
    try {
      const response = await userApi.getContractors()
      const users = response.data.results || response.data
      setContractors(users)
    } catch (error) {
      console.error('加载承建方用户失败:', error)
    } finally {
      setLoadingContractors(false)
    }
  }

  const loadRecords = async () => {
    setLoading(true)
    try {
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
      
      const response = await maintenanceApi.getRecords(params)
      if (response.data.results) {
        setRecords(response.data.results)
        setPagination(prev => ({
          ...prev,
          total: response.data.count || 0,
        }))
      } else {
        setRecords(response.data)
        setPagination(prev => ({
          ...prev,
          total: response.data.length || 0,
        }))
      }
    } catch (error) {
      console.error('加载运维记录失败:', error)
      message.error('加载运维记录失败')
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

  const handleDelete = async (id) => {
    try {
      await maintenanceApi.deleteRecord(id)
      message.success('删除成功')
      loadRecords()
    } catch (error) {
      message.error('删除失败: ' + (error.response?.data?.error || error.message))
    }
  }

  const getStatusTag = (status) => {
    const statusMap = {
      completed: { color: 'success', text: '已完成' },
      in_progress: { color: 'processing', text: '处理中' },
      pending: { color: 'warning', text: '待处理' },
      cancelled: { color: 'default', text: '已取消' },
    }
    const statusInfo = statusMap[status] || { color: 'default', text: status }
    return <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
  }

  const columns = [
    {
      title: '序号',
      dataIndex: 'sequence_number',
      key: 'sequence_number',
      width: 80,
    },
    {
      title: '区划',
      dataIndex: 'region',
      key: 'region',
      width: 120,
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      width: 120,
    },
    {
      title: '处理人',
      dataIndex: 'handler',
      key: 'handler',
      width: 120,
      render: (handler) => getUserDisplayName(handler),
    },
    {
      title: '问题描述',
      dataIndex: 'issue_description',
      key: 'issue_description',
      ellipsis: true,
    },
    {
      title: '完成情况',
      dataIndex: 'completion_status',
      key: 'completion_status',
      width: 100,
      render: (status) => getStatusTag(status),
    },
    {
      title: '完成时间',
      dataIndex: 'completion_time',
      key: 'completion_time',
      width: 180,
      render: (time) => (time ? formatDateTime(time) : '-'),
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
      width: 150,
      fixed: 'right',
      render: (_, record) => {
        // 判断当前用户是否是处理人
        const isHandler = record.handler?.id === user?.id
        
        return (
          <Space>
            {isHandler ? (
              <>
                <Button 
                  type="link" 
                  icon={<EditOutlined />}
                  onClick={() => navigate(`/maintenance/records/${record.id}/edit`)}
                >
                  编辑
                </Button>
                <Popconfirm
                  title="确定要删除这条运维记录吗？"
                  onConfirm={() => handleDelete(record.id)}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button 
                    type="link" 
                    danger
                    icon={<DeleteOutlined />}
                  >
                    删除
                  </Button>
                </Popconfirm>
              </>
            ) : (
              <Button 
                type="link" 
                icon={<EyeOutlined />}
                onClick={() => navigate(`/maintenance/records/${record.id}`)}
              >
                查看
              </Button>
            )}
          </Space>
        )
      },
    },
  ]

  if (!canAccess) {
    return null
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
        <Space wrap size="middle">
          <Space direction="vertical" size="small" style={{ marginBottom: 0 }}>
            <span style={{ fontSize: 12, color: '#666' }}>搜索</span>
            <Search
              placeholder="区划/部门/需求提出人/问题描述"
              allowClear
              style={{ width: 250 }}
              value={filters.search}
              onChange={(e) => {
                const newFilters = { ...filters, search: e.target.value }
                setFilters(newFilters)
              }}
              onSearch={() => {
                setPagination(prev => ({ ...prev, current: 1 }))
                loadRecords()
              }}
            />
          </Space>
          <Space direction="vertical" size="small" style={{ marginBottom: 0 }}>
            <span style={{ fontSize: 12, color: '#666' }}>问题类型</span>
            <Select
              style={{ width: 120 }}
              placeholder="请选择"
              allowClear
              value={filters.issue_type}
              onChange={(value) => {
                const newFilters = { ...filters, issue_type: value || '' }
                setFilters(newFilters)
                setPagination(prev => ({ ...prev, current: 1 }))
              }}
            >
              <Option value="user_consultation">用户咨询</Option>
              <Option value="new_feature">新增功能</Option>
              <Option value="program_issue">程序问题</Option>
              <Option value="implementation">实施定制</Option>
              <Option value="data_issue">数据问题</Option>
              <Option value="statistics">统计类</Option>
              <Option value="simple_training">简单培训</Option>
              <Option value="troubleshooting">故障排查</Option>
              <Option value="technical_support">技术支持</Option>
              <Option value="account_issue">账号问题</Option>
              <Option value="other">其他</Option>
            </Select>
          </Space>
          <Space direction="vertical" size="small" style={{ marginBottom: 0 }}>
            <span style={{ fontSize: 12, color: '#666' }}>完成情况</span>
            <Select
              style={{ width: 120 }}
              placeholder="请选择"
              allowClear
              value={filters.completion_status}
              onChange={(value) => {
                const newFilters = { ...filters, completion_status: value || '' }
                setFilters(newFilters)
                setPagination(prev => ({ ...prev, current: 1 }))
              }}
            >
              <Option value="completed">已完成</Option>
              <Option value="in_progress">处理中</Option>
              <Option value="pending">待处理</Option>
              <Option value="cancelled">已取消</Option>
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
            <span style={{ fontSize: 12, color: '#666' }}>处理人</span>
            <Select
              style={{ width: 150 }}
              placeholder="请选择处理人"
              allowClear
              loading={loadingContractors}
              showSearch
              filterOption={(input, option) =>
                (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
              }
              value={filters.handler}
              onChange={(value) => {
                const newFilters = { ...filters, handler: value || '' }
                setFilters(newFilters)
                setPagination(prev => ({ ...prev, current: 1 }))
              }}
            >
              {contractors.map(contractor => {
                const displayName = contractor.full_name || contractor.first_name || contractor.username
                return (
                  <Option key={contractor.id} value={contractor.id.toString()}>
                    {displayName}
                  </Option>
                )
              })}
            </Select>
          </Space>
          <Space direction="vertical" size="small" style={{ marginBottom: 0 }}>
            <span style={{ fontSize: 12, color: '#666' }}>日期范围</span>
            <RangePicker
              style={{ width: 250 }}
              value={
                filters.start_date && filters.end_date
                  ? [dayjs(filters.start_date), dayjs(filters.end_date)]
                  : null
              }
              onChange={(dates) => {
                const newFilters = {
                  ...filters,
                  start_date: dates ? dates[0].format('YYYY-MM-DD') : '',
                  end_date: dates ? dates[1].format('YYYY-MM-DD') : '',
                }
                setFilters(newFilters)
                setPagination(prev => ({ ...prev, current: 1 }))
              }}
            />
          </Space>
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/maintenance/records/create')}>
          录入运维记录
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={records}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1500 }}
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

export default MaintenanceRecordList
