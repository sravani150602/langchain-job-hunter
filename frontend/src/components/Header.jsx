import { RefreshCw, BrainCircuit } from 'lucide-react'
import { useState } from 'react'
import axios from 'axios'
import { useQueryClient } from '@tanstack/react-query'

export default function Header({ status, onRefreshComplete, activeTab, onTabChange }) {
  const [refreshing, setRefreshing] = useState(false)
  const queryClient = useQueryClient()

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await axios.post('/api/jobs/refresh/sync', null, { timeout: 120000 })
      await queryClient.invalidateQueries({ queryKey: ['jobs'] })
      await queryClient.invalidateQueries({ queryKey: ['status'] })
      if (onRefreshComplete) onRefreshComplete()
    } catch (e) {
      console.error('Refresh failed:', e)
    } finally {
      setRefreshing(false)
    }
  }

  const TABS = [
    { id: 'jobs', label: 'Jobs' },
    { id: 'resume', label: 'Resume' },
    { id: 'tracker', label: 'Tracker' },
  ]

  return (
    <header className="sticky top-0 z-50 bg-gray-950/95 backdrop-blur border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
        {/* Logo */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <div className="bg-blue-600 p-2 rounded-lg">
            <BrainCircuit className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-white text-lg leading-none">CareerCopilot AI</h1>
            <p className="text-xs text-gray-500 mt-0.5">AI-powered job search · Fresh grad focused</p>
          </div>
        </div>

        {/* Nav tabs */}
        <nav className="flex gap-1">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Refresh + status */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <div className="hidden md:flex items-center gap-1 text-xs text-gray-500">
            <span>{status?.total_jobs ?? 0} jobs</span>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing || status?.is_refreshing}
            className="btn-primary"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Fetching...' : 'Refresh Jobs'}
          </button>
        </div>
      </div>
    </header>
  )
}
