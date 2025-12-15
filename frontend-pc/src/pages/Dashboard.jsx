import { Card, Row, Col, Statistic, Spin, Empty } from 'antd'
import { FileTextOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { useEffect, useMemo, useState } from 'react'
import { Pie, Column } from '@ant-design/plots'
import { taskApi } from '../api/tasks'
import { useAuthStore } from '../store/authStore'
import dayjs from 'dayjs'

const statusMap = {
  draft: '草稿',
  pending_review: '待审核',
  reviewed: '已审核',
  assigned: '已指派',
  in_progress: '处理中',
  completed: '已完成',
  confirmed: '已确认',
  closed: '已结单',
}

const typeMap = {
  problem: '问题',
  requirement: '需求',
}

const priorityMap = {
  low: '低',
  medium: '中',
  high: '高',
  urgent: '紧急',
}

function Dashboard() {
  const { user } = useAuthStore()
  const displayName = user?.full_name || user?.first_name || user?.last_name || user?.username || '用户'
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    pending: 0,
  })

  useEffect(() => {
    loadStats()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadStats = async () => {
    setLoading(true)
    try {
      const response = await taskApi.getTasks({ page_size: 1000 })
      const result = response.data
      const taskList = result.results || result || []

      if (!Array.isArray(taskList)) {
        console.error('任务数据格式错误:', taskList)
        setTasks([])
        setStats({ total: 0, completed: 0, pending: 0 })
        return
      }

      setTasks(taskList)
      setStats({
        total: taskList.length,
        completed: taskList.filter(t => t && (t.status === 'confirmed' || t.status === 'closed')).length,
        pending: taskList.filter(t => t && ['pending_review', 'reviewed', 'assigned', 'in_progress'].includes(t.status)).length,
      })
    } catch (error) {
      console.error('加载统计失败:', error)
      setTasks([])
      setStats({ total: 0, completed: 0, pending: 0 })
    } finally {
      setLoading(false)
    }
  }

  const buildPieData = (key, map) => {
    const counter = tasks.reduce((acc, task) => {
      const value = task?.[key]
      if (!value) return acc
      const label = map[value] || value
      acc[label] = (acc[label] || 0) + 1
      return acc
    }, {})
    return Object.entries(counter).map(([type, value]) => ({ type, value }))
  }

  const statusData = useMemo(() => buildPieData('status', statusMap), [tasks])
  const typeData = useMemo(() => buildPieData('task_type', typeMap), [tasks])
  const priorityData = useMemo(() => buildPieData('priority', priorityMap), [tasks])

  const dateData = useMemo(() => {
    const counter = {}
    tasks.forEach(task => {
      if (!task?.created_at) return
      const date = dayjs(task.created_at).format('YYYY-MM-DD')
      counter[date] = (counter[date] || 0) + 1
    })
    return Object.entries(counter)
      .map(([date, value]) => ({ date, value }))
      .sort((a, b) => dayjs(a.date).valueOf() - dayjs(b.date).valueOf())
      .slice(-10) // 最近10天
  }, [tasks])

const renderChart = (title, chart, hasData) => (
  <Card
    title={title}
    variant="outlined"
    className="dashboard-chart-card"
    styles={{ body: { height: 320 } }}
  >
    {!hasData ? <Empty description="暂无数据" /> : chart}
  </Card>
)

  return (
    <div>
      <h2 style={{ fontWeight: 500 }}>欢迎，{displayName}</h2>
      <Spin spinning={loading}>
        <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
          <Col span={8}>
            <Card>
              <Statistic
                title="总任务数"
                value={stats.total}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="已完成"
                value={stats.completed}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="待处理"
                value={stats.pending}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
          <Col xs={24} md={12}>
            {renderChart(
              '按状态统计任务数',
              <Pie
                data={statusData}
                angleField="value"
                colorField="type"
                radius={0.9}
                label={false}
                legend={{
                  position: 'right',
                }}
                interactions={[{ type: 'element-active' }]}
                animation={{ appear: { animation: 'wave-in' } }}
              />,
              statusData.length > 0
            )}
          </Col>
          <Col xs={24} md={12}>
            {renderChart(
              '按类型统计任务数',
              <Pie
                data={typeData}
                angleField="value"
                colorField="type"
                radius={0.9}
                innerRadius={0.6}
                statistic={{
                  title: false,
                  content: {
                    content: '任务类型',
                  },
                }}
                label={false}
                legend={{
                  position: 'right',
                }}
                interactions={[{ type: 'element-selected' }]}
              />,
              typeData.length > 0
            )}
          </Col>
          <Col xs={24} md={12}>
            {renderChart(
              '按优先级统计任务数',
              <Pie
                data={priorityData}
                angleField="value"
                colorField="type"
                radius={0.9}
                label={false}
                legend={{ position: 'right' }}
              />,
              priorityData.length > 0
            )}
          </Col>
          <Col xs={24} md={12}>
            {renderChart(
              '按日期统计任务数',
              <Column
                data={dateData}
                xField="date"
                yField="value"
                columnStyle={{ radius: [6, 6, 0, 0] }}
                color="#1677ff"
                tooltip={{ title: '日期', formatter: datum => ({ name: '任务数', value: datum.value }) }}
              />,
              dateData.length > 0
            )}
          </Col>
        </Row>
      </Spin>
    </div>
  )
}

export default Dashboard

