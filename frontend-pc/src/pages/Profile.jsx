import { Card, Descriptions, Button, Form, Input, message } from 'antd'
import { useEffect, useState } from 'react'
import { userApi } from '../api/users'
import { useAuthStore } from '../store/authStore'

function Profile() {
  const { user, setUser } = useAuthStore()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) {
      form.setFieldsValue(user)
    }
  }, [user, form])

  const onFinish = async (values) => {
    setLoading(true)
    try {
      const response = await userApi.updateUser(user.id, values)
      setUser(response.data)
      message.success('更新成功')
    } catch (error) {
      message.error('更新失败')
    } finally {
      setLoading(false)
    }
  }

  const handleChangePassword = async (values) => {
    try {
      await userApi.changePassword(values)
      message.success('密码修改成功')
    } catch (error) {
      message.error(error.response?.data?.error || '密码修改失败')
    }
  }

  if (!user) return <div>加载中...</div>

  return (
    <div>
      <Card title="个人信息">
        <Descriptions column={2} bordered>
          <Descriptions.Item label="用户名">{user.username}</Descriptions.Item>
          <Descriptions.Item label="角色">{user.role_display}</Descriptions.Item>
          <Descriptions.Item label="邮箱">{user.email}</Descriptions.Item>
          <Descriptions.Item label="手机号">{user.phone || '-'}</Descriptions.Item>
          <Descriptions.Item label="部门">{user.department || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="修改信息" style={{ marginTop: 24 }}>
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="email" label="邮箱">
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="手机号">
            <Input />
          </Form.Item>
          <Form.Item name="department" label="部门">
            <Input />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              保存
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="修改密码" style={{ marginTop: 24 }}>
        <Form layout="vertical" onFinish={handleChangePassword}>
          <Form.Item name="old_password" label="原密码" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="new_password" label="新密码" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="new_password_confirm" label="确认新密码" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">
              修改密码
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Profile

