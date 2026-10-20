import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './caresphere.css'
import './electronics-inspired.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
