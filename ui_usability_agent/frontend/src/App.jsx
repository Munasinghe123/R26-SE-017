import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import PreviewPage from './pages/PreviewPage'
import ReportPage from './pages/ReportPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/preview/:screenId" element={<PreviewPage />} />
        <Route path="/reports/:screenId" element={<ReportPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App