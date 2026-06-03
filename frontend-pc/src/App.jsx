import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Login from './pages/Login'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import TaskList from './pages/TaskList'
import TaskDetail from './pages/TaskDetail'
import TaskCreate from './pages/TaskCreate'
import Profile from './pages/Profile'
import MaintenanceRecordList from './pages/MaintenanceRecordList'
import MaintenanceRecordCreate from './pages/MaintenanceRecordCreate'
import MaintenanceRecordDetail from './pages/MaintenanceRecordDetail'
import MaintenanceReport from './pages/MaintenanceReport'

function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/login" />
}

function CreateTaskRoute({ children }) {
  const { user } = useAuthStore()
  // 只有使用方和管理员可以访问创建任务页面
  const canCreateTask = user?.role === 'user' || user?.role === 'admin'
  return canCreateTask ? children : <Navigate to="/tasks" replace />
}

function MaintenanceRoute({ children }) {
  const { user } = useAuthStore()
  // 只有承建方（项目经理和员工）可以访问运维记录
  const canAccess = user?.role === 'manager' || user?.role === 'employee'
  return canAccess ? children : <Navigate to="/" replace />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="tasks" element={<TaskList />} />
          <Route path="tasks/create" element={
            <CreateTaskRoute>
              <TaskCreate />
            </CreateTaskRoute>
          } />
          <Route path="tasks/:id" element={<TaskDetail />} />
          <Route path="profile" element={<Profile />} />
          <Route path="maintenance/records" element={
            <MaintenanceRoute>
              <MaintenanceRecordList />
            </MaintenanceRoute>
          } />
          <Route path="maintenance/records/create" element={
            <MaintenanceRoute>
              <MaintenanceRecordCreate />
            </MaintenanceRoute>
          } />
          <Route path="maintenance/records/:id/edit" element={
            <MaintenanceRoute>
              <MaintenanceRecordCreate />
            </MaintenanceRoute>
          } />
          <Route path="maintenance/records/:id" element={
            <MaintenanceRoute>
              <MaintenanceRecordDetail />
            </MaintenanceRoute>
          } />
          <Route path="maintenance/report" element={
            <MaintenanceRoute>
              <MaintenanceReport />
            </MaintenanceRoute>
          } />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

