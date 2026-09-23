import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import PersonDetail from './pages/PersonDetail.jsx'

export default function App() {
  return (
    <div className="min-h-screen bg-neutral-950 font-tajawal text-neutral-100" dir="rtl">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/person/:id" element={<PersonDetail />} />
        </Routes>
      </BrowserRouter>
    </div>
  )
}
