import { Card, Descriptions, Tag, Button, Space, Form, Input, message, Timeline, Modal, Select, List, Popconfirm, Upload } from 'antd'
import { DownloadOutlined, DeleteOutlined, PaperClipOutlined, EditOutlined, UploadOutlined } from '@ant-design/icons'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { taskApi } from '../api/tasks'
import { useAuthStore } from '../store/authStore'
import { workflowApi } from '../api/workflow'
import { userApi } from '../api/users'
import { formatDateTime, getUserDisplayName } from '../utils/format'

const { TextArea } = Input

function TaskDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuthStore()
  const [task, setTask] = useState(null)
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState([])
  const [commentForm] = Form.useForm()
  const [assignModalVisible, setAssignModalVisible] = useState(false)
  const [assignForm] = Form.useForm()
  const [employees, setEmployees] = useState([])
  const [employeesLoading, setEmployeesLoading] = useState(false)
  const [completeModalVisible, setCompleteModalVisible] = useState(false)
  const [completeForm] = Form.useForm()
  const [handleModalVisible, setHandleModalVisible] = useState(false)
  const [handleForm] = Form.useForm()
  const [confirmModalVisible, setConfirmModalVisible] = useState(false)
  const [confirmForm] = Form.useForm()
  const [confirmType, setConfirmType] = useState(null) // 'approve' 或 'reject'
  const [assistantModalVisible, setAssistantModalVisible] = useState(false)
  const [assistantForm] = Form.useForm()
  const [reviewModalVisible, setReviewModalVisible] = useState(false)
  const [reviewForm] = Form.useForm()
  const [reviewType, setReviewType] = useState(null) // 'approve' 或 'reject'
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [editForm] = Form.useForm()
  const [draftUploadList, setDraftUploadList] = useState([])
  const [draftUploading, setDraftUploading] = useState(false)

  useEffect(() => {
    loadTask()
    loadLogs()
  }, [id])

  useEffect(() => {
    // 当任务状态为已审核或已指派，且当前用户是项目经理时，预加载员工列表
    if ((task?.status === 'reviewed' || task?.status === 'assigned') && user?.role === 'manager') {
      loadEmployees()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [task?.status, user?.role])

  const loadTask = async () => {
    try {
      const response = await taskApi.getTask(id)
      setTask(response.data)
    } catch (error) {
      message.error('加载任务失败')
    }
  }

  const loadLogs = async () => {
    try {
      const response = await workflowApi.getWorkflowLogs({ task_id: id })
      setLogs(response.data.results || response.data)
    } catch (error) {
      console.error('加载日志失败:', error)
    }
  }

  const handleReview = async (values) => {
    setLoading(true)
    try {
      const approved = reviewType === 'approve'
      await taskApi.reviewTask(id, { 
        approved, 
        review_comment: values.review_comment || '' 
      })
      message.success(approved ? '审核通过' : '审核不通过')
      setReviewModalVisible(false)
      reviewForm.resetFields()
      loadTask()
    } catch (error) {
      const errorMsg = error.response?.data?.review_comment?.[0] || error.response?.data?.error || '操作失败'
      message.error(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const openReviewModal = (type) => {
    setReviewType(type)
    setReviewModalVisible(true)
  }

  const handleStartHandle = async (values) => {
    setLoading(true)
    try {
      await taskApi.handleTask(id, {
        handle_comment: values.handle_comment || ''
      })
      message.success('任务已开始处理')
      setHandleModalVisible(false)
      handleForm.resetFields()
      loadTask()
    } catch (error) {
      message.error(error.response?.data?.error || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  const handleComplete = async (values) => {
    setLoading(true)
    try {
      await taskApi.completeTask(id, {
        handle_comment: values?.handle_comment || ''
      })
      message.success('任务已标记为完成')
      setCompleteModalVisible(false)
      completeForm.resetFields()
      loadTask()
    } catch (error) {
      message.error(error.response?.data?.error || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirm = async (values) => {
    setLoading(true)
    try {
      const confirmed = confirmType === 'approve'
      await taskApi.confirmTask(id, { 
        confirmed, 
        confirm_comment: values.confirm_comment || '' 
      })
      message.success(confirmed ? '确认完成' : '修改意见已提交')
      setConfirmModalVisible(false)
      confirmForm.resetFields()
      loadTask()
      loadLogs() // 重新加载工作流日志
    } catch (error) {
      const errorMsg = error.response?.data?.confirm_comment?.[0] || error.response?.data?.error || '操作失败'
      message.error(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const openConfirmModal = (type) => {
    setConfirmType(type)
    setConfirmModalVisible(true)
  }

  const handleAddComment = async (values) => {
    try {
      await taskApi.addComment(id, values)
      message.success('评论添加成功')
      commentForm.resetFields()
      loadTask()
    } catch (error) {
      message.error('添加评论失败')
    }
  }

  const loadEmployees = async () => {
    setEmployeesLoading(true)
    try {
      const response = await userApi.getEmployees()
      setEmployees(response.data || [])
    } catch (error) {
      console.error('加载员工列表失败:', error)
      message.error('加载员工列表失败')
    } finally {
      setEmployeesLoading(false)
    }
  }

  const handleAssign = async (values) => {
    setLoading(true)
    try {
      await taskApi.assignTask(id, {
        handler_id: values.handler_id,
        task_type: values.task_type || undefined,
        assign_comment: values.assign_comment || ''
      })
      const messageText = task?.status === 'assigned' ? '任务重新指派成功' : '任务指派成功'
      message.success(messageText)
      setAssignModalVisible(false)
      assignForm.resetFields()
      loadTask()
      loadLogs() // 重新加载工作流日志
    } catch (error) {
      message.error(error.response?.data?.error || '指派失败')
    } finally {
      setLoading(false)
    }
  }

  const openAssignModal = () => {
    setAssignModalVisible(true)
    // 重置表单，清除之前选择的值
    assignForm.resetFields()
    if (employees.length === 0) {
      loadEmployees()
    }
  }

  const openAssistantModal = () => {
    setAssistantModalVisible(true)
    // 设置表单初始值为当前协助员工
    assistantForm.setFieldsValue({
      assistant_employee_ids: task?.assistant_employees?.map(emp => emp.id) || []
    })
    if (employees.length === 0) {
      loadEmployees()
    }
  }

  const handleSetAssistants = async (values) => {
    setLoading(true)
    try {
      await taskApi.setAssistants(id, {
        assistant_employee_ids: values.assistant_employee_ids || []
      })
      message.success('协助员工设置成功')
      setAssistantModalVisible(false)
      assistantForm.resetFields()
      loadTask()
      loadLogs() // 重新加载工作流日志
    } catch (error) {
      message.error(error.response?.data?.error || '设置失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadAttachment = async (attachmentId) => {
    try {
      const response = await taskApi.downloadAttachment(id, attachmentId)
      // 创建blob URL并下载
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      
      // 从响应头获取文件名，或者使用附件信息
      const attachment = task.attachments.find(a => a.id === attachmentId)
      link.download = attachment?.original_filename || 'attachment'
      
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      message.success('下载开始')
    } catch (error) {
      message.error('下载失败: ' + (error.response?.data?.error || '下载失败'))
    }
  }

  const handleDeleteAttachment = async (attachmentId) => {
    try {
      await taskApi.deleteAttachment(id, attachmentId)
      message.success('附件已删除')
      loadTask()
    } catch (error) {
      message.error('删除失败: ' + (error.response?.data?.error || '删除失败'))
    }
  }

  if (!task) return <div>加载中...</div>

  // 判断当前用户是否为协助员工
  const isAssistant = task?.assistant_employees?.some(emp => emp.id === user?.id)
  // 判断当前用户是否为处理人
  const isHandler = task?.handler?.id === user?.id

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
  
  const handleSubmitDraft = async () => {
    setLoading(true)
    try {
      await taskApi.submitDraft(id)
      message.success('草稿提交成功')
      loadTask()
      loadLogs()
    } catch (error) {
      message.error(error.response?.data?.error || '提交失败')
    } finally {
      setLoading(false)
    }
  }
  
  const handleEditDraft = () => {
    // 设置表单初始值（不包含任务类型，任务类型由项目经理在指派时设置）
    editForm.setFieldsValue({
      title: task.title,
      description: task.description,
      priority: task.priority,
    })
    setEditModalVisible(true)
  }
  
  const handleUpdateDraft = async (values) => {
    setLoading(true)
    try {
      await taskApi.updateTask(id, values)
      message.success('草稿更新成功')
      setEditModalVisible(false)
      editForm.resetFields()
      loadTask()
    } catch (error) {
      message.error(error.response?.data?.error || '更新失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDraftUploadChange = ({ fileList }) => {
    setDraftUploadList(fileList)
  }

  const handleDraftUpload = async () => {
    if (draftUploadList.length === 0) {
      message.warning('请选择要上传的附件')
      return
    }
    setDraftUploading(true)
    let successCount = 0
    let failCount = 0
    for (const file of draftUploadList) {
      try {
        const fileObj = file.originFileObj || file
        if (!fileObj) {
          throw new Error('文件对象不存在')
        }
        await taskApi.uploadAttachment(id, fileObj)
        successCount++
      } catch (error) {
        failCount++
        message.error(`上传附件 ${file.name} 失败：${error.response?.data?.error || error.message || '上传失败'}`)
      }
    }
    setDraftUploading(false)
    setDraftUploadList([])
    if (successCount > 0) {
      message.success(`成功上传 ${successCount} 个附件`)
      loadTask()
    }
    if (failCount > 0 && successCount === 0) {
      message.error('附件上传失败，请稍后重试')
    }
  }

  return (
    <div>
      <Card
        title={task.title}
        extra={
          <Button 
            onClick={() => {
              // 如果有返回URL（从任务列表跳转过来），使用返回URL
              // 否则使用默认的/tasks
              const returnUrl = location.state?.returnUrl || '/tasks'
              navigate(returnUrl)
            }}
          >
            返回列表
          </Button>
        }
      >
        <Descriptions column={2} bordered>
          <Descriptions.Item label="任务类型">
            {task.task_type_display || (task.task_type ? (task.task_type === 'problem' ? '问题' : '需求') : '未设置')}
          </Descriptions.Item>
          <Descriptions.Item label="状态">{getStatusTag(task.status)}</Descriptions.Item>
          <Descriptions.Item label="优先级">{task.priority_display}</Descriptions.Item>
          <Descriptions.Item label="创建人">{getUserDisplayName(task.creator)}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{formatDateTime(task.created_at)}</Descriptions.Item>
          {task.reviewer && <Descriptions.Item label="审核人">{getUserDisplayName(task.reviewer)}</Descriptions.Item>}
          {task.handler && <Descriptions.Item label="处理人">{getUserDisplayName(task.handler)}</Descriptions.Item>}
          {task.assistant_employees && task.assistant_employees.length > 0 && (
            <Descriptions.Item label="协助员工">
              {task.assistant_employees.map(emp => getUserDisplayName(emp)).join('、')}
            </Descriptions.Item>
          )}
          {isAssistant && (
            <Descriptions.Item label="您的角色">
              <Tag color="blue">协助员工（仅可查看）</Tag>
            </Descriptions.Item>
          )}
          {task.updated_at && <Descriptions.Item label="更新时间">{formatDateTime(task.updated_at)}</Descriptions.Item>}
          {task.closed_at && <Descriptions.Item label="结单时间">{formatDateTime(task.closed_at)}</Descriptions.Item>}
        </Descriptions>

        <div style={{ marginTop: 24 }}>
          <h3>任务描述</h3>
          <p>{task.description}</p>
        </div>

        {/* 附件列表 */}
        {task.attachments && task.attachments.length > 0 && (
          <div style={{ marginTop: 24 }}>
            <h3>附件</h3>
            <List
              bordered
              dataSource={task.attachments}
              renderItem={(attachment) => {
                const canDelete = (task.status === 'pending_review' || task.status === 'draft') && 
                  (user?.role === 'user' || user?.role === 'admin') && 
                  (task.creator?.id === user?.id || user?.role === 'admin')
                
                return (
                  <List.Item
                    actions={[
                      <Button
                        type="link"
                        icon={<DownloadOutlined />}
                        onClick={() => handleDownloadAttachment(attachment.id)}
                      >
                        下载
                      </Button>,
                      canDelete && (
                        <Popconfirm
                          title="确定要删除这个附件吗？"
                          onConfirm={() => handleDeleteAttachment(attachment.id)}
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
                      ),
                    ].filter(Boolean)}
                  >
                    <Space>
                      <PaperClipOutlined />
                      <span>{attachment.original_filename}</span>
                      <span style={{ color: '#999', fontSize: 12 }}>
                        {attachment.file_size_display}
                      </span>
                      <span style={{ color: '#999', fontSize: 12 }}>
                        上传人: {getUserDisplayName(attachment.uploaded_by)}
                      </span>
                      <span style={{ color: '#999', fontSize: 12 }}>
                        {formatDateTime(attachment.created_at)}
                      </span>
                    </Space>
                  </List.Item>
                )
              }}
            />
          </div>
        )}
        {task.status === 'draft' && (user?.role === 'user' || user?.role === 'admin') && 
         (task.creator?.id === user?.id || user?.role === 'admin') && (
          <div style={{ marginTop: 16 }}>
            <h4>草稿附件管理</h4>
            <Upload
              fileList={draftUploadList}
              beforeUpload={() => false}
              onChange={handleDraftUploadChange}
              multiple
            >
              <Button icon={<UploadOutlined />}>选择附件</Button>
            </Upload>
            <div style={{ marginTop: 8 }}>
              <Button
                type="primary"
                disabled={draftUploadList.length === 0}
                loading={draftUploading}
                onClick={handleDraftUpload}
              >
                上传附件
              </Button>
              <span style={{ marginLeft: 12, color: '#999' }}>草稿阶段可自由上传或删除附件</span>
            </div>
          </div>
        )}

        {/* 草稿任务操作按钮 */}
        {task.status === 'draft' && (user?.role === 'user' || user?.role === 'admin') && 
         (task.creator?.id === user?.id || user?.role === 'admin') && (
          <div style={{ marginTop: 24 }}>
            <Space>
              <Button icon={<EditOutlined />} onClick={handleEditDraft} loading={loading}>
                编辑草稿
              </Button>
              <Button type="primary" onClick={handleSubmitDraft} loading={loading}>
                提交草稿
              </Button>
            </Space>
          </div>
        )}

        {task.status === 'pending_review' && user?.role === 'admin' && (
          <div style={{ marginTop: 24 }}>
            <Space>
              <Button type="primary" onClick={() => openReviewModal('approve')} loading={loading}>
                审核通过
              </Button>
              <Button danger onClick={() => openReviewModal('reject')} loading={loading}>
                审核不通过
              </Button>
            </Space>
          </div>
        )}

        {/* 显示审核不通过理由（任务状态为已结单时，对所有用户可见，但对创建人特别突出） */}
        {task.status === 'closed' && task.review_comment && (
          <div style={{ 
            marginTop: 24, 
            padding: 16, 
            background: task.creator?.id === user?.id ? '#fff7e6' : '#f5f5f5', 
            border: task.creator?.id === user?.id ? '1px solid #ffd591' : '1px solid #d9d9d9', 
            borderRadius: 4 
          }}>
            <h4 style={{ color: task.creator?.id === user?.id ? '#d46b08' : '#595959', marginBottom: 8 }}>
              {task.creator?.id === user?.id ? '审核不通过理由' : '审核意见'}
            </h4>
            <p style={{ 
              color: task.creator?.id === user?.id ? '#614700' : '#262626', 
              whiteSpace: 'pre-wrap',
              margin: 0
            }}>{task.review_comment}</p>
          </div>
        )}

        {/* 显示审核意见（审核通过时，如果填写了审核意见） */}
        {task.review_comment && task.status !== 'closed' && (
          <div style={{ marginTop: 24 }}>
            <h4>审核意见</h4>
            <p style={{ whiteSpace: 'pre-wrap', padding: 12, background: '#f5f5f5', borderRadius: 4, margin: 0 }}>{task.review_comment}</p>
          </div>
        )}

        {task.status === 'reviewed' && user?.role === 'manager' && (
          <div style={{ marginTop: 24 }}>
            <Button type="primary" onClick={openAssignModal} loading={loading}>
              指派给员工
            </Button>
          </div>
        )}

        {task.status === 'assigned' && user?.role === 'manager' && (
          <div style={{ marginTop: 24 }}>
            <Button type="primary" onClick={openAssignModal} loading={loading}>
              重新指派
            </Button>
          </div>
        )}

        {task.status === 'assigned' && isHandler && (
          <div style={{ marginTop: 24 }}>
            <Space>
              <Button type="primary" onClick={() => setHandleModalVisible(true)} loading={loading}>
                开始处理
              </Button>
              <Button onClick={openAssistantModal} loading={loading}>
                设置协助员工
              </Button>
            </Space>
          </div>
        )}

        {task.status === 'in_progress' && isHandler && (
          <div style={{ marginTop: 24 }}>
            <Space>
              <Button type="primary" onClick={() => setCompleteModalVisible(true)} loading={loading}>
                标记完成
              </Button>
              <Button onClick={openAssistantModal} loading={loading}>
                设置协助员工
              </Button>
            </Space>
          </div>
        )}

        {task.status === 'completed' && task.creator?.id === user?.id && (
          <div style={{ marginTop: 24 }}>
            <Space>
              <Button type="primary" onClick={() => openConfirmModal('approve')} loading={loading}>
                确认完成
              </Button>
              <Button danger onClick={() => openConfirmModal('reject')} loading={loading}>
                需要修改
              </Button>
            </Space>
          </div>
        )}

        {/* 显示修改意见（需要修改时，四方都能看到） */}
        {task.confirm_comment && task.status === 'in_progress' && (
          <div style={{ marginTop: 24, padding: 16, background: '#fff1f0', border: '1px solid #ffccc7', borderRadius: 4 }}>
            <h4 style={{ color: '#cf1322', marginBottom: 8 }}>修改意见</h4>
            <div style={{ color: '#8c8c8c', fontSize: 12, marginBottom: 8 }}>
              由 {getUserDisplayName(task.creator)} 提出
            </div>
            <p style={{ color: '#262626', whiteSpace: 'pre-wrap', margin: 0 }}>{task.confirm_comment}</p>
          </div>
        )}

        {/* 显示确认意见（确认完成时） */}
        {task.confirm_comment && task.status === 'confirmed' && (
          <div style={{ marginTop: 24 }}>
            <h4>确认意见</h4>
            <p style={{ whiteSpace: 'pre-wrap', padding: 12, background: '#f5f5f5', borderRadius: 4, margin: 0 }}>{task.confirm_comment}</p>
          </div>
        )}

        <div style={{ marginTop: 24 }}>
          <h3>评论</h3>
          {task.comments?.map((comment) => (
            <Card key={comment.id} size="small" style={{ marginBottom: 8 }}>
              <div><strong>{getUserDisplayName(comment.user)}</strong> - {formatDateTime(comment.created_at)}</div>
              <div>{comment.content}</div>
            </Card>
          ))}
          <Form form={commentForm} onFinish={handleAddComment} style={{ marginTop: 16 }}>
            <Form.Item name="content" rules={[{ required: true, message: '请输入评论内容' }]}>
              <TextArea rows={3} placeholder="添加评论..." />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit">提交评论</Button>
            </Form.Item>
          </Form>
        </div>

        <div style={{ marginTop: 24 }}>
          <h3>工作流日志</h3>
          <Timeline>
            {logs.map((log) => (
              <Timeline.Item key={log.id}>
                <div><strong>{getUserDisplayName(log.user)}</strong> - {log.action}</div>
                <div style={{ color: '#999', fontSize: 12 }}>{formatDateTime(log.created_at)}</div>
                {log.comment && <div>{log.comment}</div>}
              </Timeline.Item>
            ))}
          </Timeline>
        </div>
      </Card>

      {/* 指派任务弹窗 */}
      <Modal
        title={task?.status === 'assigned' ? '重新指派任务' : '指派任务给员工'}
        open={assignModalVisible}
        onCancel={() => {
          setAssignModalVisible(false)
          assignForm.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={assignForm}
          onFinish={handleAssign}
          layout="vertical"
        >
          {task?.status === 'assigned' && task?.handler && (
            <div style={{ marginBottom: 16, padding: 12, background: '#fff7e6', borderRadius: 4 }}>
              <div style={{ color: '#d46b08', marginBottom: 4 }}>当前处理人：</div>
              <div>{getUserDisplayName(task.handler)}</div>
            </div>
          )}
          {/* 如果任务类型为空，显示任务类型选择（首次指派时必填） */}
          {!task?.task_type && (
            <Form.Item
              name="task_type"
              label="任务类型"
              rules={[{ required: true, message: '请选择任务类型' }]}
            >
              <Select placeholder="请选择任务类型">
                <Select.Option value="problem">问题</Select.Option>
                <Select.Option value="requirement">需求</Select.Option>
              </Select>
            </Form.Item>
          )}
          {/* 如果任务已有类型，显示当前类型（只读） */}
          {task?.task_type && (
            <Form.Item label="任务类型">
              <Tag color={task.task_type === 'problem' ? 'red' : 'blue'}>
                {task.task_type === 'problem' ? '问题' : '需求'}
              </Tag>
            </Form.Item>
          )}
          <Form.Item
            name="handler_id"
            label={task?.status === 'assigned' ? '选择新员工' : '选择员工'}
            rules={[{ required: true, message: '请选择员工' }]}
          >
            <Select
              placeholder="请选择员工"
              loading={employeesLoading}
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={employees
                .filter(emp => !task?.handler || emp.id !== task.handler.id) // 重新指派时，排除当前处理人
                .map(emp => ({
                  value: emp.id,
                  label: `${emp.full_name || emp.username}${emp.department ? ` (${emp.department})` : ''}`
                }))}
            />
          </Form.Item>
          <Form.Item
            name="assign_comment"
            label={task?.status === 'assigned' ? '重新指派说明（可选）' : '指派说明（可选）'}
          >
            <TextArea rows={4} placeholder={task?.status === 'assigned' ? '请输入重新指派的原因...' : '请输入指派说明...'} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                {task?.status === 'assigned' ? '确认重新指派' : '确认指派'}
              </Button>
              <Button onClick={() => {
                setAssignModalVisible(false)
                assignForm.resetFields()
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
          </Modal>

      {/* 开始处理弹窗 */}
      <Modal
        title="开始处理任务"
        open={handleModalVisible}
        onCancel={() => {
          setHandleModalVisible(false)
          handleForm.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={handleForm}
          onFinish={handleStartHandle}
          layout="vertical"
        >
          <Form.Item
            name="handle_comment"
            label="处理说明（可选）"
          >
            <TextArea rows={4} placeholder="请输入处理说明..." />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                确认开始
              </Button>
              <Button onClick={() => {
                setHandleModalVisible(false)
                handleForm.resetFields()
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 标记完成弹窗 */}
      <Modal
        title="标记任务完成"
        open={completeModalVisible}
        onCancel={() => {
          setCompleteModalVisible(false)
          completeForm.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={completeForm}
          onFinish={handleComplete}
          layout="vertical"
        >
          <Form.Item
            name="handle_comment"
            label="处理说明（可选）"
          >
            <TextArea rows={4} placeholder="请输入处理说明或完成情况..." />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                确认完成
              </Button>
              <Button onClick={() => {
                setCompleteModalVisible(false)
                completeForm.resetFields()
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
          </Form>
      </Modal>

      {/* 审核任务弹窗 */}
      <Modal
        title={reviewType === 'approve' ? '审核通过' : '审核不通过'}
        open={reviewModalVisible}
        onCancel={() => {
          setReviewModalVisible(false)
          reviewForm.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={reviewForm}
          onFinish={handleReview}
          layout="vertical"
        >
          <Form.Item
            name="review_comment"
            label={reviewType === 'approve' ? '审核意见（可选）' : '不通过理由（必填）'}
            rules={reviewType === 'reject' ? [{ required: true, message: '请填写不通过理由' }] : []}
          >
            <TextArea 
              rows={4} 
              placeholder={reviewType === 'approve' ? '请输入审核意见...' : '请详细说明不通过的原因...'} 
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                确认{reviewType === 'approve' ? '通过' : '不通过'}
              </Button>
              <Button onClick={() => {
                setReviewModalVisible(false)
                reviewForm.resetFields()
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 确认任务弹窗 */}
      <Modal
        title={confirmType === 'approve' ? '确认任务完成' : '填写修改意见'}
        open={confirmModalVisible}
        onCancel={() => {
          setConfirmModalVisible(false)
          confirmForm.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={confirmForm}
          onFinish={handleConfirm}
          layout="vertical"
        >
          <Form.Item
            name="confirm_comment"
            label={confirmType === 'approve' ? '确认意见（可选）' : '修改意见（必填）'}
            rules={confirmType === 'reject' ? [{ required: true, message: '请填写修改意见' }] : []}
          >
            <TextArea 
              rows={4} 
              placeholder={confirmType === 'approve' ? '请输入确认意见...' : '请详细说明需要修改的内容...'} 
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                {confirmType === 'approve' ? '确认完成' : '提交修改意见'}
              </Button>
              <Button onClick={() => {
                setConfirmModalVisible(false)
                confirmForm.resetFields()
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 设置协助员工弹窗 */}
      <Modal
        title="设置协助员工"
        open={assistantModalVisible}
        onCancel={() => {
          setAssistantModalVisible(false)
          assistantForm.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={assistantForm}
          onFinish={handleSetAssistants}
          layout="vertical"
        >
          <div style={{ marginBottom: 16, padding: 12, background: '#e6f7ff', border: '1px solid #91d5ff', borderRadius: 4 }}>
            <p style={{ margin: 0, fontSize: 12, color: '#595959' }}>
              协助员工可以查看任务详情，但无法进行任何操作（开始处理、标记完成等）。只有您（处理人）可以操作任务。
            </p>
          </div>
          <Form.Item
            name="assistant_employee_ids"
            label="选择协助员工（可多选）"
          >
            <Select
              mode="multiple"
              placeholder="请选择协助员工（可不选）"
              loading={employeesLoading}
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={employees
                .filter(emp => emp.id !== task?.handler?.id) // 排除处理人自己
                .map(emp => ({
                  value: emp.id,
                  label: `${emp.full_name || emp.username}${emp.department ? ` (${emp.department})` : ''}`
                }))}
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                确认设置
              </Button>
              <Button onClick={() => {
                setAssistantModalVisible(false)
                assistantForm.resetFields()
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑草稿弹窗 */}
      <Modal
        title="编辑草稿"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false)
          editForm.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={editForm}
          onFinish={handleUpdateDraft}
          layout="vertical"
        >
          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: '请输入标题!' }]}
          >
            <Input placeholder="请输入任务标题" />
          </Form.Item>

          <Form.Item
            name="priority"
            label="优先级"
          >
            <Select>
              <Select.Option value="low">低</Select.Option>
              <Select.Option value="medium">中</Select.Option>
              <Select.Option value="high">高</Select.Option>
              <Select.Option value="urgent">紧急</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
            rules={[{ required: true, message: '请输入描述!' }]}
          >
            <TextArea rows={6} placeholder="请输入任务详细描述" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                保存
              </Button>
              <Button onClick={() => {
                setEditModalVisible(false)
                editForm.resetFields()
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TaskDetail

