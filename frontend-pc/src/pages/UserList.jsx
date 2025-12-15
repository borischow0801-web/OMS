import { Table, Button, Tag, message } from 'antd'
import { useEffect, useState } from 'react'
import { userApi } from '../api/users'

function UserList() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    setLoading(true)
    try {
      const response = await userApi.getUsers()
      setUsers(response.data.results || response.data)
    } catch (error) {
      message.error('加载用户失败')
    } finally {
      setLoading(false)
    }
  }

  const getRoleTag = (role) => {
    const roleMap = {
      user: { color: 'blue', text: '使用方' },
      admin: { color: 'red', text: '管理方' },
      manager: { color: 'orange', text: '项目经理' },
      employee: { color: 'green', text: '员工' },
    }
    const roleInfo = roleMap[role] || { color: 'default', text: role }
    return <Tag color={roleInfo.color}>{roleInfo.text}</Tag>
  }

  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role) => getRoleTag(role),
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      key: 'phone',
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
  ]

  return (
    <div>
      <Table
        columns={columns}
        dataSource={users}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20 }}
      />
    </div>
  )
}

export default UserList

