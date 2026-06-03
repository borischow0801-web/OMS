import { Form, Input, Select, Button, Card, message, DatePicker, Space, Row, Col, Upload, List, Typography, Popconfirm } from 'antd'
import { UploadOutlined, DeleteOutlined, PaperClipOutlined, DownloadOutlined, PlusOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import { maintenanceApi } from '../api/maintenance'
import { userApi } from '../api/users'
import { useState, useEffect } from 'react'
import { useAuthStore } from '../store/authStore'
import dayjs from 'dayjs'

const { TextArea } = Input
const { Option } = Select

// 区划选项
const REGION_OPTIONS = [
  '威海市',
  '环翠区',
  '文登区',
  '荣成市',
  '乳山市',
  '高区',
  '经区',
  '临港区',
]

// 功能模块选项
const FUNCTIONAL_MODULE_OPTIONS = [
  '综合受理',
  '事项管理',
  '网上审批',
  '工程审批',
  '电子证照',
  '政务服务网',
  '一链办理',
  '省中台',
  '云勘验',
  '审管互动',
  '涉企平台',
  '大屏',
  '自助终端',
  'bsp',
  '统一排队',
  '多图联审',
  '一窗通',
  '受理审批',
  '表单2.0',
  '业务中台',
  '标准事项',
  '授权委托',
  '其他',
]

function MaintenanceRecordCreate() {
  const navigate = useNavigate()
  const { id } = useParams()
  const { user } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [contractors, setContractors] = useState([])
  const [loadingContractors, setLoadingContractors] = useState(false)
  const [pendingFiles, setPendingFiles] = useState([])
  const [existingAttachments, setExistingAttachments] = useState([])
  const [completionStatus, setCompletionStatus] = useState('pending')
  // 更新内容动态行：{key, id?, content, update_time (dayjs)}
  const [updateLogs, setUpdateLogs] = useState([])
  const [form] = Form.useForm()
  const isEdit = !!id

  // 只有承建方可以访问
  const canAccess = user?.role === 'manager' || user?.role === 'employee'

  useEffect(() => {
    if (!canAccess) {
      message.error('您没有权限访问运维记录')
      navigate('/maintenance/records')
      return
    }

    loadContractors().then(() => {
      if (isEdit) {
        loadRecord()
      }
    })
  }, [id, canAccess, navigate, isEdit])

  const loadContractors = async () => {
    setLoadingContractors(true)
    try {
      const response = await userApi.getContractors()
      const users = response.data.results || response.data
      setContractors(users.filter(u => u.id !== user?.id))
    } catch (error) {
      console.error('加载承建方用户失败:', error)
    } finally {
      setLoadingContractors(false)
    }
  }

  const loadRecord = async () => {
    try {
      const response = await maintenanceApi.getRecord(id)
      const record = response.data

      // 非本人录入的记录跳转只读详情页
      if (record.creator?.id !== user?.id) {
        navigate(`/maintenance/records/${id}`)
        return
      }

      let assistantIds = record.assistant_user_ids || []
      if (assistantIds.length === 0 && record.assistant && Array.isArray(record.assistant) && record.assistant.length > 0) {
        assistantIds = record.assistant
          .map(username => {
            const assistantUser = contractors.find(c => c.username === username)
            return assistantUser?.id
          })
          .filter(id => id !== undefined)
      }

      const status = record.completion_status || 'pending'
      setCompletionStatus(status)

      form.setFieldsValue({
        region: record.region,
        department: record.department,
        requester: record.requester,
        request_date: record.request_date ? dayjs(record.request_date) : null,
        issue_type: record.issue_type,
        functional_module: record.functional_module,
        issue_description: record.issue_description,
        priority: record.priority,
        completion_status: status,
        completion_time: record.completion_time ? dayjs(record.completion_time) : null,
        assistant: assistantIds,
      })

      setExistingAttachments(record.attachments || [])

      setUpdateLogs(
        (record.update_logs || []).map(log => ({
          key: log.id,
          id: log.id,
          content: log.content,
          update_time: dayjs(log.update_time),
        }))
      )
    } catch (error) {
      message.error('加载运维记录失败')
      navigate('/maintenance/records')
    }
  }

  // 下载已有附件
  const handleDownloadAttachment = async (attachment) => {
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

  // 删除已有附件（立即调用接口）
  const handleDeleteExistingAttachment = async (attachmentId) => {
    try {
      await maintenanceApi.deleteAttachment(id, attachmentId)
      setExistingAttachments(prev => prev.filter(a => a.id !== attachmentId))
      message.success('附件已删除')
    } catch (error) {
      message.error(error.response?.data?.error || '删除失败')
    }
  }

  // 上传待上传文件到指定记录ID
  const uploadPendingFiles = async (recordId) => {
    if (pendingFiles.length === 0) return
    const results = await Promise.allSettled(
      pendingFiles.map(file => maintenanceApi.uploadAttachment(recordId, file))
    )
    const failed = results.filter(r => r.status === 'rejected').length
    if (failed > 0) {
      message.warning(`${pendingFiles.length - failed} 个文件上传成功，${failed} 个文件上传失败`)
    } else {
      message.success(`${pendingFiles.length} 个附件上传成功`)
    }
  }

  // 更新内容：新增一行
  const handleAddUpdateLog = () => {
    setUpdateLogs(prev => [
      ...prev,
      { key: Date.now(), content: '', update_time: dayjs() },
    ])
  }

  // 更新内容：修改某行字段
  const handleUpdateLogChange = (key, field, value) => {
    setUpdateLogs(prev =>
      prev.map(log => (log.key === key ? { ...log, [field]: value } : log))
    )
  }

  // 更新内容：删除某行
  const handleDeleteUpdateLog = (key) => {
    setUpdateLogs(prev => prev.filter(log => log.key !== key))
  }

  const onFinish = async (values, addNew = false) => {
    // 校验更新内容：不允许内容为空的行
    const emptyLog = updateLogs.find(log => !log.content || !log.content.trim())
    if (emptyLog) {
      message.error('更新内容不能为空，请填写或删除空行')
      return
    }

    setLoading(true)
    try {
      const data = {
        region: values.region,
        department: values.department,
        requester: values.requester,
        request_date: values.request_date ? values.request_date.format('YYYY-MM-DD') : null,
        issue_type: values.issue_type,
        functional_module: values.functional_module,
        issue_description: values.issue_description,
        priority: values.priority,
        completion_status: values.completion_status,
        completion_time: values.completion_time ? values.completion_time.toISOString() : null,
        assistant: (values.assistant && Array.isArray(values.assistant))
          ? values.assistant.filter(id => id && id > 0)
          : [],
        update_logs: updateLogs.map(log => ({
          content: log.content,
          update_time: log.update_time.toISOString(),
        })),
      }

      if (isEdit) {
        await maintenanceApi.updateRecord(id, data)
        await uploadPendingFiles(id)
        message.success('更新成功')
        if (!addNew) {
          setTimeout(() => navigate('/maintenance/records'), 1000)
        }
      } else {
        const response = await maintenanceApi.createRecord(data)
        const newRecordId = response.data.id
        await uploadPendingFiles(newRecordId)
        message.success('创建成功')

        if (addNew) {
          form.resetFields()
          form.setFieldsValue({
            priority: 'medium',
            completion_status: 'pending',
            request_date: dayjs(),
          })
          setCompletionStatus('pending')
          setPendingFiles([])
          setUpdateLogs([])
        } else {
          setTimeout(() => navigate('/maintenance/records'), 1000)
        }
      }
    } catch (error) {
      const errorMessage =
        error.response?.data?.error ||
        error.response?.data?.completion_time?.[0] ||
        error.response?.data?.assistant?.[0] ||
        error.response?.data?.detail ||
        error.message ||
        (isEdit ? '更新失败' : '创建失败')
      message.error(errorMessage)
      console.error('操作失败:', error.response?.data || error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitAndAddNew = async () => {
    try {
      const values = await form.validateFields()
      await onFinish(values, true)
    } catch (error) {
      if (error.errorFields) {
        message.warning('请完善必填项')
      }
    }
  }

  if (!canAccess) {
    return null
  }

  return (
    <Card title={isEdit ? '编辑运维记录' : '录入运维记录'}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          priority: 'medium',
          completion_status: 'pending',
          request_date: dayjs(),
        }}
        onValuesChange={(changedValues) => {
          if ('completion_status' in changedValues) {
            const newStatus = changedValues.completion_status
            setCompletionStatus(newStatus)
            if (newStatus === 'completed') {
              if (!form.getFieldValue('completion_time')) {
                form.setFieldValue('completion_time', dayjs())
              }
            } else {
              form.setFieldValue('completion_time', null)
            }
          }
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="区划"
              name="region"
              rules={[{ required: true, message: '请选择区划' }]}
            >
              <Select placeholder="请选择区划">
                {REGION_OPTIONS.map(region => (
                  <Option key={region} value={region}>{region}</Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="部门" name="department">
              <Input placeholder="请输入部门" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="需求提出人" name="requester">
              <Input placeholder="请输入需求提出人" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="需求提出日期"
              name="request_date"
              rules={[{ required: true, message: '请选择需求提出日期' }]}
            >
              <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="问题类型"
              name="issue_type"
              rules={[{ required: true, message: '请选择问题类型' }]}
            >
              <Select placeholder="请选择问题类型">
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
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="功能模块" name="functional_module">
              <Select placeholder="请选择功能模块" showSearch allowClear>
                {FUNCTIONAL_MODULE_OPTIONS.map(module => (
                  <Option key={module} value={module}>{module}</Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          label="问题描述"
          name="issue_description"
          rules={[{ required: true, message: '请输入问题描述' }]}
        >
          <TextArea rows={4} placeholder="请输入问题描述" />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="优先级"
              name="priority"
              rules={[{ required: true, message: '请选择优先级' }]}
            >
              <Select>
                <Option value="low">低</Option>
                <Option value="medium">中</Option>
                <Option value="high">高</Option>
                <Option value="urgent">紧急</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="协助人" name="assistant">
              <Select
                mode="multiple"
                placeholder="请选择协助人（可多选）"
                allowClear
                loading={loadingContractors}
                showSearch
                filterOption={(input, option) =>
                  (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                }
              >
                {contractors.map(contractor => {
                  const roleDisplay = contractor.role === 'manager' ? '项目经理' : contractor.role === 'employee' ? '员工' : contractor.role
                  const displayName = contractor.full_name || contractor.first_name || contractor.username
                  return (
                    <Option key={contractor.id} value={contractor.id}>
                      {displayName} ({roleDisplay})
                    </Option>
                  )
                })}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="完成情况"
              name="completion_status"
              rules={[{ required: true, message: '请选择完成情况' }]}
            >
              <Select>
                <Option value="completed">已完成</Option>
                <Option value="in_progress">处理中</Option>
                <Option value="pending">待处理</Option>
                <Option value="cancelled">已取消</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="完成时间"
              name="completion_time"
              rules={[
                {
                  required: completionStatus === 'completed',
                  message: '完成情况为已完成时，完成时间为必填项',
                },
              ]}
            >
              <DatePicker
                showTime
                style={{ width: '100%' }}
                format="YYYY-MM-DD HH:mm:ss"
                disabled={completionStatus !== 'completed'}
                placeholder={completionStatus === 'completed' ? '请选择完成时间' : '仅完成情况为"已完成"时可填'}
              />
            </Form.Item>
          </Col>
        </Row>

        {/* 附件 */}
        <Form.Item label="附件">
          {isEdit && existingAttachments.length > 0 && (
            <List
              size="small"
              style={{ marginBottom: 8, border: '1px solid #f0f0f0', borderRadius: 6, padding: '4px 0' }}
              dataSource={existingAttachments}
              renderItem={item => (
                <List.Item
                  actions={[
                    <Button
                      type="link"
                      size="small"
                      icon={<DownloadOutlined />}
                      onClick={() => handleDownloadAttachment(item)}
                    >
                      下载
                    </Button>,
                    <Popconfirm
                      title="确定要删除该附件吗？"
                      onConfirm={() => handleDeleteExistingAttachment(item.id)}
                      okText="确定"
                      cancelText="取消"
                    >
                      <Button type="link" danger size="small" icon={<DeleteOutlined />}>
                        删除
                      </Button>
                    </Popconfirm>,
                  ]}
                >
                  <PaperClipOutlined style={{ marginRight: 6 }} />
                  <Typography.Text>{item.original_filename}</Typography.Text>
                  <Typography.Text type="secondary" style={{ marginLeft: 8 }}>
                    ({item.file_size_display})
                  </Typography.Text>
                </List.Item>
              )}
            />
          )}
          {isEdit && existingAttachments.length === 0 && (
            <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
              暂无附件
            </Typography.Text>
          )}
          {pendingFiles.length > 0 && (
            <List
              size="small"
              style={{ marginBottom: 8 }}
              dataSource={pendingFiles}
              renderItem={(file, index) => (
                <List.Item
                  actions={[
                    <Button
                      type="link"
                      danger
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={() => setPendingFiles(prev => prev.filter((_, i) => i !== index))}
                    >
                      移除
                    </Button>,
                  ]}
                >
                  <PaperClipOutlined style={{ marginRight: 6 }} />
                  <Typography.Text>{file.name}</Typography.Text>
                </List.Item>
              )}
            />
          )}
          <Upload
            beforeUpload={(file) => {
              setPendingFiles(prev => [...prev, file])
              return false
            }}
            showUploadList={false}
            multiple
          >
            <Button icon={<UploadOutlined />}>选择文件</Button>
          </Upload>
          {pendingFiles.length > 0 && (
            <Typography.Text type="secondary" style={{ marginLeft: 8 }}>
              已选择 {pendingFiles.length} 个文件，提交后自动上传
            </Typography.Text>
          )}
        </Form.Item>

        {/* 更新内容 */}
        <Form.Item label="更新内容">
          {updateLogs.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              {updateLogs.map(log => (
                <Row key={log.key} gutter={8} style={{ marginBottom: 8, alignItems: 'flex-start' }}>
                  <Col flex="1">
                    <TextArea
                      rows={2}
                      placeholder="请输入更新内容"
                      value={log.content}
                      onChange={e => handleUpdateLogChange(log.key, 'content', e.target.value)}
                    />
                  </Col>
                  <Col style={{ width: 200 }}>
                    <DatePicker
                      showTime
                      style={{ width: '100%' }}
                      format="YYYY-MM-DD HH:mm"
                      value={log.update_time}
                      onChange={val => handleUpdateLogChange(log.key, 'update_time', val || dayjs())}
                    />
                  </Col>
                  <Col>
                    <Button
                      type="link"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => handleDeleteUpdateLog(log.key)}
                    />
                  </Col>
                </Row>
              ))}
            </div>
          )}
          <Button icon={<PlusOutlined />} onClick={handleAddUpdateLog}>
            更新内容
          </Button>
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>
              {isEdit ? '更新' : '提交'}
            </Button>
            {!isEdit && (
              <Button type="primary" onClick={handleSubmitAndAddNew} loading={loading}>
                提交并新增
              </Button>
            )}
            <Button onClick={() => navigate('/maintenance/records')}>
              取消
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  )
}

export default MaintenanceRecordCreate
