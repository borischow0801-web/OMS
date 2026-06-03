import { Card, Statistic, Tag, message, Spin, Row, Col, Empty } from 'antd'
import { useEffect, useState } from 'react'
import { maintenanceApi } from '../api/maintenance'
import { useAuthStore } from '../store/authStore'
import { useNavigate } from 'react-router-dom'
import { Pie, Bar, Column, Line } from '@ant-design/plots'

function MaintenanceReport() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [statistics, setStatistics] = useState(null)
  
  // 只有承建方可以访问
  const canAccess = user?.role === 'manager' || user?.role === 'employee'
  
  useEffect(() => {
    if (!canAccess) {
      message.error('您没有权限访问运维记录报告')
      navigate('/')
      return
    }
    loadStatistics()
  }, [canAccess, navigate])

  const loadStatistics = async () => {
    setLoading(true)
    try {
      const response = await maintenanceApi.getStatistics()
      setStatistics(response.data)
      // 调试信息：检查数据格式
      console.log('统计数据:', response.data)
      console.log('事件类型数据:', response.data?.issue_type_statistics)
      console.log('完成情况数据:', response.data?.completion_status_statistics)
      console.log('功能模块数据:', response.data?.functional_module_statistics)
    } catch (error) {
      console.error('加载统计报告失败:', error)
      message.error('加载统计报告失败')
    } finally {
      setLoading(false)
    }
  }

  if (!canAccess) {
    return null
  }

  // 按事件类型统计数据处理
  const issueTypeData = (statistics?.issue_type_statistics || [])
    .map((item) => {
      if (!item) return null
      const count = Number(item.count) || 0
      if (isNaN(count) || count <= 0) return null
      const type = item.issue_type_display || item.issue_type || '其他'
      return { type, count }
    })
    .filter(Boolean)
  
  // 调试：检查处理后的数据
  if (statistics) {
    console.log('处理后的按事件类型数据:', issueTypeData)
  }

  // 按完成情况统计数据处理
  const completionStatusData = (statistics?.completion_status_statistics || [])
    .map((item) => {
      if (!item) return null
      const count = Number(item.count) || 0
      if (isNaN(count) || count <= 0) return null
      const status = item.completion_status_display || item.completion_status || '其他'
      return { status, count }
    })
    .filter(Boolean)
  
  // 调试：检查处理后的数据
  if (statistics) {
    console.log('处理后的按完成情况数据:', completionStatusData)
  }

  const handlerData = (statistics?.handler_statistics || [])
    .filter(item => item && (item.count > 0 || item.handler_display || item.handler_username))
    .map((item) => ({
      handler: item.handler_display || item.handler_username || '未指定',
      count: Number(item.count) || 0,
    }))
    .filter(item => item.count > 0)

  const regionData = (statistics?.region_statistics || [])
    .filter(item => item && (item.count > 0 || item.region))
    .map((item) => ({
      region: item.region || '其他',
      count: Number(item.count) || 0,
    }))
    .filter(item => item.count > 0)

  const monthData = (statistics?.request_month_statistics || [])
    .filter(item => item && (item.count > 0 || item.month))
    .map((item) => ({
      month: item.month || '未知',
      count: Number(item.count) || 0,
    }))
    .filter(item => item.count > 0)

  // 按功能模块统计数据处理
  const moduleData = (statistics?.functional_module_statistics || [])
    .map((item) => {
      if (!item) return null
      const count = Number(item.count) || 0
      if (isNaN(count) || count <= 0) return null
      const module = item.functional_module || '其他'
      return { module, count }
    })
    .filter(Boolean)
  
  // 调试：检查处理后的数据
  if (statistics) {
    console.log('处理后的按功能模块数据:', moduleData)
  }

  const totalCount = statistics?.total_count || 0
  const completedCount = statistics?.completed_count || 0

  const issueTypePieConfig = issueTypeData.length > 0 ? {
    data: issueTypeData,
    angleField: 'count',
    colorField: 'type',
    radius: 0.9,
    innerRadius: 0.6,
    legend: { position: 'bottom' },
    label: false,
    statistic: {
      title: { content: '事件类型' },
      content: { content: `${totalCount} 个` },
    },
    interactions: [{ type: 'element-active' }],
  } : null

  const completionPieConfig = completionStatusData.length > 0 ? {
    data: completionStatusData,
    angleField: 'count',
    colorField: 'status',
    radius: 0.9,
    innerRadius: 0.6,
    legend: { position: 'bottom' },
    label: false,
    statistic: {
      title: { content: '完成情况' },
      content: { content: `${completedCount} / ${totalCount}` },
    },
    interactions: [{ type: 'element-active' }],
  } : null

  const handlerBarConfig = {
    data: handlerData,
    xField: 'count',
    yField: 'handler',
    seriesField: 'handler',
    legend: false,
    maxBarWidth: 24,
    label: { position: 'right' },
    tooltip: { showMarkers: false },
    yAxis: { label: { autoHide: true, autoRotate: false } },
  }

  const regionColumnConfig = {
    data: regionData,
    xField: 'region',
    yField: 'count',
    label: { position: 'top' },
    xAxis: { label: { autoHide: true, autoRotate: true } },
    tooltip: { showMarkers: false },
  }

  const monthLineConfig = {
    data: monthData,
    xField: 'month',
    yField: 'count',
    point: { size: 4, shape: 'diamond' },
    tooltip: { showMarkers: true },
    xAxis: { label: { autoHide: true, autoRotate: true } },
  }

  const modulePieConfig = moduleData.length > 0 ? {
    data: moduleData,
    angleField: 'count',
    colorField: 'module',
    radius: 0.9,
    innerRadius: 0.55,
    legend: { position: 'bottom' },
    label: false,
    interactions: [{ type: 'element-active' }],
  } : null

  return (
    <div>
      <Spin spinning={loading}>
        <div style={{ marginBottom: 24 }}>
          <h2>运维记录报告</h2>
        </div>

        <div style={{ marginBottom: 24 }}>
          <Card>
            <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
              <Statistic
                title="总事件数"
                value={statistics?.total_count || 0}
                suffix="个"
                valueStyle={{ color: '#1890ff' }}
              />
              <Statistic
                title="完成数"
                value={statistics?.completed_count || 0}
                suffix="个"
                valueStyle={{ color: '#52c41a' }}
              />
              <Statistic
                title="未完成数"
                value={statistics?.incomplete_count || 0}
                suffix="个"
                valueStyle={{ color: '#ff4d4f' }}
              />
            </div>
          </Card>
        </div>

        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card title="按事件类型统计">
              {!issueTypePieConfig || issueTypeData.length === 0 ? (
                <Empty description="暂无数据" />
              ) : (
                <div style={{ height: '400px' }}>
                  <Pie {...issueTypePieConfig} />
                </div>
              )}
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="按完成情况统计">
              {!completionPieConfig || completionStatusData.length === 0 ? (
                <Empty description="暂无数据" />
              ) : (
                <div style={{ height: '400px' }}>
                  <Pie {...completionPieConfig} />
                </div>
              )}
              <div style={{ marginTop: 12 }}>
                <Tag color="success">已完成：{statistics?.completed_count || 0}</Tag>
                <Tag color="error">未完成：{statistics?.incomplete_count || 0}</Tag>
                <Tag color="default">总计：{statistics?.total_count || 0}</Tag>
              </div>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="按处理人员统计">
              {!handlerData || handlerData.length === 0 ? <Empty description="暂无数据" /> : <Bar {...handlerBarConfig} />}
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="按区划统计">
              {!regionData || regionData.length === 0 ? <Empty description="暂无数据" /> : <Column {...regionColumnConfig} />}
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="按需求提出日期统计">
              {!monthData || monthData.length === 0 ? <Empty description="暂无数据" /> : <Line {...monthLineConfig} />}
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="按功能模块统计">
              {!modulePieConfig || moduleData.length === 0 ? (
                <Empty description="暂无数据" />
              ) : (
                <div style={{ height: '400px' }}>
                  <Pie {...modulePieConfig} />
                </div>
              )}
            </Card>
          </Col>
        </Row>
      </Spin>
    </div>
  )
}

export default MaintenanceReport
