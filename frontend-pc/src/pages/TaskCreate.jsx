import { Form, Input, Select, Button, Card, message, Result, Upload, Space, List } from 'antd'
import { UploadOutlined, DeleteOutlined, PaperClipOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { taskApi } from '../api/tasks'
import { useState, useEffect } from 'react'
import { useAuthStore } from '../store/authStore'

const { TextArea } = Input
const { Option } = Select

function TaskCreate() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [taskId, setTaskId] = useState(null)
  const [fileList, setFileList] = useState([])
  const [uploading, setUploading] = useState(false)
  const [form] = Form.useForm()
  
  // 检查用户权限：只有使用方和管理员可以创建任务
  const canCreateTask = user?.role === 'user' || user?.role === 'admin'
  
  useEffect(() => {
    if (!canCreateTask) {
      message.error('您没有权限创建任务')
      navigate('/tasks')
    }
  }, [canCreateTask, navigate])
  
  // 如果没有权限，显示错误页面
  if (!canCreateTask) {
    return (
      <Card>
        <Result
          status="403"
          title="403"
          subTitle="抱歉，您没有权限创建任务。只有使用方和管理员可以创建任务。"
          extra={
            <Button type="primary" onClick={() => navigate('/tasks')}>
              返回任务列表
            </Button>
          }
        />
      </Card>
    )
  }

  const onFinish = async (values, saveAsDraft = false) => {
    setLoading(true)
    try {
      const response = await taskApi.createTask({
        ...values,
        save_as_draft: saveAsDraft
      })
      const newTaskId = response.data?.id
      setTaskId(newTaskId)
      message.success(saveAsDraft ? '草稿保存成功' : '任务创建成功')
      
      // 如果有文件，上传附件（草稿也可以上传附件）
      if (fileList.length > 0) {
        setUploading(true)
        let successCount = 0
        let failCount = 0
        for (const file of fileList) {
          try {
            // Ant Design Upload组件的文件对象，originFileObj是原始文件对象
            const fileObj = file.originFileObj || file
            if (!fileObj) {
              console.error('文件对象不存在:', file)
              failCount++
              message.error(`上传附件 ${file.name} 失败: 文件对象不存在`)
              continue
            }
            await taskApi.uploadAttachment(newTaskId, fileObj)
            successCount++
          } catch (error) {
            failCount++
            console.error('上传附件失败:', error)
            const errorMsg = error.response?.data?.error || error.message || '上传失败'
            message.error(`上传附件 ${file.name} 失败: ${errorMsg}`)
          }
        }
        setUploading(false)
        if (failCount === 0) {
          message.success(`所有附件上传完成（${successCount}个）`)
        } else if (successCount > 0) {
          message.warning(`部分附件上传失败：成功 ${successCount} 个，失败 ${failCount} 个`)
        } else {
          message.error('所有附件上传失败')
        }
      }
      
      // 延迟跳转，让用户看到成功消息
      setTimeout(() => {
        navigate('/tasks')
      }, 1000)
    } catch (error) {
      message.error(error.response?.data?.error || (saveAsDraft ? '保存草稿失败' : '创建失败'))
    } finally {
      setLoading(false)
    }
  }
  
  const handleSaveDraft = async () => {
    try {
      // 获取表单值，不验证必填字段（草稿可以不填完整）
      const values = await form.validateFields().catch(() => form.getFieldsValue())
      await onFinish(values, true) // 第二个参数表示保存为草稿
    } catch (error) {
      // 即使验证失败，也尝试保存草稿（使用已填写的值）
      const values = form.getFieldsValue()
      if (values.title || values.description) {
        await onFinish(values, true)
      } else {
        message.warning('请至少填写标题或描述才能保存草稿')
      }
    }
  }
  
  const handleFileChange = ({ fileList: newFileList }) => {
    setFileList(newFileList)
  }
  
  const handleRemove = (file) => {
    const newFileList = fileList.filter(item => item.uid !== file.uid)
    setFileList(newFileList)
  }
  
  const uploadProps = {
    multiple: true,
    fileList,
    onChange: handleFileChange,
    onRemove: handleRemove,
    beforeUpload: () => false, // 阻止自动上传
  }

  return (
    <Card title="创建任务">
      <Form
        form={form}
        layout="vertical"
        onFinish={(values) => onFinish(values, false)}
        autoComplete="off"
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
          initialValue="medium"
        >
          <Select>
            <Option value="low">低</Option>
            <Option value="medium">中</Option>
            <Option value="high">高</Option>
            <Option value="urgent">紧急</Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="description"
          label="描述"
          rules={[{ required: true, message: '请输入描述!' }]}
        >
          <TextArea rows={6} placeholder="请输入任务详细描述" />
        </Form.Item>

        <Form.Item
          label="附件"
          help="支持上传任何格式的文件，任务提交后只能查看和下载，不能删除"
        >
          <Upload {...uploadProps}>
            <Button icon={<UploadOutlined />}>选择文件</Button>
          </Upload>
          {fileList.length > 0 && (
            <List
              size="small"
              style={{ marginTop: 8 }}
              dataSource={fileList}
              renderItem={(file) => (
                <List.Item
                  actions={[
                    <Button
                      type="link"
                      danger
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={() => handleRemove(file)}
                    >
                      删除
                    </Button>
                  ]}
                >
                  <Space>
                    <PaperClipOutlined />
                    <span>{file.name}</span>
                    <span style={{ color: '#999', fontSize: 12 }}>
                      {(file.size / 1024).toFixed(2)} KB
                    </span>
                  </Space>
                </List.Item>
              )}
            />
          )}
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading || uploading}>
              {uploading ? '上传附件中...' : '提交'}
            </Button>
            <Button onClick={handleSaveDraft} loading={loading || uploading}>
              保存草稿
            </Button>
            <Button onClick={() => navigate('/tasks')}>
              取消
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  )
}

export default TaskCreate

