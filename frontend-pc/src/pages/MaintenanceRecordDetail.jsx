import { Card, Descriptions, Tag, Button, Space, message, Table, Upload, Popconfirm, Typography } from 'antd'
import { ArrowLeftOutlined, UploadOutlined, DownloadOutlined, DeleteOutlined, PaperClipOutlined } from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { maintenanceApi } from '../api/maintenance'
import { useAuthStore } from '../store/authStore'
import { formatDateTime, getUserDisplayName } from '../utils/format'
import dayjs from 'dayjs'

function MaintenanceRecordDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [record, setRecord] = useState(null)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)

  // 只有本人录入的记录才能上传/删除附件；下载对所有承建方开放
  const canManageAttachment = record?.creator?.id === user?.id

  useEffect(() => {
    loadRecord()
  }, [id])

  const loadRecord = async () => {
    setLoading(true)
    try {
      const response = await maintenanceApi.getRecord(id)
      setRecord(response.data)
    } catch (error) {
      message.error('加载运维记录失败')
      navigate('/maintenance/records')
    } finally {
      setLoading(false)
    }
  }

  const getIssueTypeTag = (type) => {
    const typeMap = {
      user_consultation: { color: 'green', text: '用户咨询' },
      new_feature: { color: 'purple', text: '新增功能' },
      program_issue: { color: 'red', text: '程序问题' },
      implementation: { color: 'blue', text: '实施定制' },
      data_issue: { color: 'orange', text: '数据问题' },
      statistics: { color: 'geekblue', text: '统计类' },
      simple_training: { color: 'cyan', text: '简单培训' },
      troubleshooting: { color: 'volcano', text: '故障排查' },
      technical_support: { color: 'lime', text: '技术支持' },
      account_issue: { color: 'gold', text: '账号问题' },
      other: { color: 'default', text: '其他' },
    }
    const typeInfo = typeMap[type] || { color: 'default', text: type }
    return <Tag color={typeInfo.color}>{typeInfo.text}</Tag>
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

  const getPriorityTag = (priority) => {
    const priorityMap = {
      low: { color: 'default', text: '低' },
      medium: { color: 'blue', text: '中' },
      high: { color: 'orange', text: '高' },
      urgent: { color: 'red', text: '紧急' },
    }
    const priorityInfo = priorityMap[priority] || { color: 'default', text: priority }
    return <Tag color={priorityInfo.color}>{priorityInfo.text}</Tag>
  }

  const handleUpload = async (file) => {
    setUploading(true)
    try {
      await maintenanceApi.uploadAttachment(id, file)
      message.success('附件上传成功')
      loadRecord()
    } catch (error) {
      message.error(error.response?.data?.error || '附件上传失败')
    } finally {
      setUploading(false)
    }
    return false
  }

  const handleDownload = async (attachment) => {
    try {
      const response = await maintenanceApi.downloadAttachment(id, attachment.id)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', attachment.original_filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      message.error('下载失败')
    }
  }

  const handleDeleteAttachment = async (attachmentId) => {
    try {
      await maintenanceApi.deleteAttachment(id, attachmentId)
      message.success('附件已删除')
      loadRecord()
    } catch (error) {
      message.error(error.response?.data?.error || '删除失败')
    }
  }

  const attachmentColumns = [
    {
      title: '文件名',
      dataIndex: 'original_filename',
      render: (name) => (
        <Space>
          <PaperClipOutlined />
          <Typography.Text>{name}</Typography.Text>
        </Space>
      ),
    },
    {
      title: '大小',
      dataIndex: 'file_size_display',
      width: 100,
    },
    {
      title: '上传人',
      dataIndex: 'uploaded_by',
      width: 120,
      render: (user) => getUserDisplayName(user),
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      width: 160,
      render: (t) => formatDateTime(t),
    },
    {
      title: '操作',
      width: 140,
      render: (_, attachment) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => handleDownload(attachment)}
          >
            下载
          </Button>
          {canManageAttachment && (
            <Popconfirm
              title="确定要删除该附件吗？"
              onConfirm={() => handleDeleteAttachment(attachment.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" danger size="small" icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  const updateLogColumns = [
    {
      title: '更新内容',
      dataIndex: 'content',
    },
    {
      title: '更新时间',
      dataIndex: 'update_time',
      width: 180,
      render: (t) => formatDateTime(t),
    },
  ]

  if (!record) {
    return null
  }

  return (
    <div>
      <Card
        title="运维记录详情"
        extra={
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/maintenance/records')}>
            返回列表
          </Button>
        }
        loading={loading}
      >
        <Descriptions column={2} bordered>
          <Descriptions.Item label="序号">{record.sequence_number || '-'}</Descriptions.Item>
          <Descriptions.Item label="区划">{record.region || '-'}</Descriptions.Item>
          <Descriptions.Item label="部门">{record.department || '-'}</Descriptions.Item>
          <Descriptions.Item label="需求提出人">{record.requester || '-'}</Descriptions.Item>
          <Descriptions.Item label="需求提出日期">
            {record.request_date ? dayjs(record.request_date).format('YYYY-MM-DD') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="问题类型">
            {getIssueTypeTag(record.issue_type)}
          </Descriptions.Item>
          <Descriptions.Item label="功能模块">{record.functional_module || '-'}</Descriptions.Item>
          <Descriptions.Item label="优先级">
            {getPriorityTag(record.priority)}
          </Descriptions.Item>
          <Descriptions.Item label="问题描述" span={2}>
            {record.issue_description || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="处理人">
            {getUserDisplayName(record.handler)}
          </Descriptions.Item>
          <Descriptions.Item label="协助人">
            {record.assistant_display && record.assistant_display.length > 0
              ? record.assistant_display.join('、')
              : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="完成情况">
            {getStatusTag(record.completion_status)}
          </Descriptions.Item>
          <Descriptions.Item label="完成时间">
            {record.completion_time ? formatDateTime(record.completion_time) : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="创建人">
            {getUserDisplayName(record.creator)}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {formatDateTime(record.created_at)}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {formatDateTime(record.updated_at)}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card
        title="附件"
        style={{ marginTop: 16 }}
        extra={
          canManageAttachment && (
            <Upload beforeUpload={handleUpload} showUploadList={false} multiple>
              <Button icon={<UploadOutlined />} loading={uploading}>
                上传附件
              </Button>
            </Upload>
          )
        }
      >
        <Table
          columns={attachmentColumns}
          dataSource={record.attachments || []}
          rowKey="id"
          pagination={false}
          locale={{ emptyText: '暂无附件' }}
          size="small"
        />
      </Card>

      <Card title="更新内容" style={{ marginTop: 16 }}>
        <Table
          columns={updateLogColumns}
          dataSource={record.update_logs || []}
          rowKey="id"
          pagination={false}
          locale={{ emptyText: '暂无更新内容' }}
          size="small"
        />
      </Card>
    </div>
  )
}

export default MaintenanceRecordDetail
