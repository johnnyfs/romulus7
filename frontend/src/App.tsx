import { Navigate, Route, Routes } from 'react-router-dom'
import WorkspacesPage from './pages/WorkspacesPage'

function App() {
  return (
      <Routes>
        <Route path="/" element={<Navigate to="/workspaces" replace />} />
        <Route path="/workspaces" element={<WorkspacesPage />} />
      </Routes>
    )
}

export default App
