import { Navigate, Route, Routes } from 'react-router-dom'
import { CategoryPage } from './pages/CategoryPage'
import { HomePage } from './pages/HomePage'
import { LevelPage } from './pages/LevelPage'
import { QuizPage } from './pages/QuizPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/category/:slug" element={<CategoryPage />} />
      <Route path="/category/:slug/level/:levelSlug" element={<LevelPage />} />
      <Route path="/quiz/:slug" element={<QuizPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
