import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ErrorBoundary } from 'react-error-boundary'
import './index.css'
import App from './App.tsx'

const ErrorFallback = ({ error }: { error: any }) => (
  <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6 text-center">
    <h2 className="text-2xl font-bold text-red-500 mb-4">Oops! Something went wrong.</h2>
    <pre className="text-xs bg-white/5 p-4 rounded-xl max-w-full overflow-auto mb-6 text-white/60">
      {error?.message || 'Unknown error'}
    </pre>
    <button
      onClick={() => window.location.href = '/'}
      className="px-6 py-3 bg-indigo-600 rounded-full font-bold hover:bg-indigo-700 transition"
    >
      Return Home
    </button>
  </div>
)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <App />
    </ErrorBoundary>
  </StrictMode>,
)
