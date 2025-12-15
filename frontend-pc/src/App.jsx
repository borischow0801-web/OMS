import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Login from './pages/Login'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import TaskList from './pages/TaskList'
import TaskDetail from './pages/TaskDetail'
import TaskCreate from './pages/TaskCreate'
import Profile from './pages/Profile'

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
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

