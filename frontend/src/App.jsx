import { useState, useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { User, Search, AlertCircle, Loader2, LayoutGrid } from 'lucide-react'
import Header from './components/Header.jsx'
import FilterPanel from './components/FilterPanel.jsx'
import JobCard from './components/JobCard.jsx'
import ProfileSetup from './components/ProfileSetup.jsx'
import ResumePage from './components/ResumePage.jsx'
import TrackerPage from './components/TrackerPage.jsx'
import JobDetailModal from './components/JobDetailModal.jsx'
import { useJobs, useStatus } from './hooks/useJobs.js'

const DEFAULT_FILTERS = {
  max_hours_ago: 48,
  job_type: '',
  priority_only: false,
  remote_only: false,
  min_score: 0,
  companies: [],
}

export default function App() {
  const [activeTab, setActiveTab] = useState('jobs')
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [searchText, setSearchText] = useState('')
  const [showProfile, setShowProfile] = useState(false)
  const [selectedJob, setSelectedJob] = useState(null)
  const queryClient = useQueryClient()

  const { data: jobs = [], isLoading, isError, error } = useJobs(filters)
  const { data: status } = useStatus()

  const displayJobs = useMemo(() => {
    let result = jobs

    if (filters.companies && filters.companies.length > 0) {
      const companiesLower = filters.companies.map(c => c.toLowerCase())
      result = result.filter(j =>
        companiesLower.some(c => j.company.toLowerCase().includes(c))
      )
    }

    if (searchText.trim()) {
      const q = searchText.toLowerCase()
      result = result.filter(j =>
        j.title.toLowerCase().includes(q) ||
        j.company.toLowerCase().includes(q) ||
        j.location?.toLowerCase().includes(q) ||
        j.job_summary?.toLowerCase().includes(q)
      )
    }

    return result
  }, [jobs, filters.companies, searchText])

  const handleProfileSave = async (profile) => {
    try {
      await fetch('/api/jobs/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile, max_hours_ago: filters.max_hours_ago, limit: 200 }),
      })
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    } catch (e) {
      console.error('Re-score failed:', e)
    }
  }

  const stats = useMemo(() => ({
    total: displayJobs.length,
    new: displayJobs.filter(j => (j.hours_ago ?? 999) < 6).length,
    highMatch: displayJobs.filter(j => (j.match_score ?? 0) >= 70).length,
    remote: displayJobs.filter(j => j.remote).length,
  }), [displayJobs])

  return (
    <div className="min-h-screen bg-gray-950">
      <Header
        status={status}
        onRefreshComplete={() => queryClient.invalidateQueries({ queryKey: ['jobs'] })}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      <div className="max-w-7xl mx-auto px-4 py-6">

        {/* ── Resume Tab ── */}
        {activeTab === 'resume' && <ResumePage />}

        {/* ── Tracker Tab ── */}
        {activeTab === 'tracker' && <TrackerPage />}

        {/* ── Jobs Tab ── */}
        {activeTab === 'jobs' && (
          <>
            {/* Search + Profile row */}
            <div className="flex gap-3 mb-6">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  type="text"
                  placeholder="Search jobs, companies, locations..."
                  value={searchText}
                  onChange={e => setSearchText(e.target.value)}
                  className="input pl-9"
                />
              </div>
              <button
                onClick={() => setShowProfile(true)}
                className="btn-secondary whitespace-nowrap"
              >
                <User className="w-4 h-4" />
                My Profile
              </button>
            </div>

            {/* Stats bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
              {[
                { label: 'Total Jobs', value: stats.total, color: 'text-white' },
                { label: 'Posted < 6h', value: stats.new, color: 'text-red-400' },
                { label: 'Strong Match (70+)', value: stats.highMatch, color: 'text-green-400' },
                { label: 'Remote', value: stats.remote, color: 'text-blue-400' },
              ].map(({ label, value, color }) => (
                <div key={label} className="card text-center py-3">
                  <div className={`text-2xl font-bold ${color}`}>{value}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{label}</div>
                </div>
              ))}
            </div>

            {/* Main layout */}
            <div className="flex gap-6">
              <FilterPanel filters={filters} onChange={setFilters} />

              <main className="flex-1 min-w-0">
                {isLoading && (
                  <div className="flex flex-col items-center justify-center py-24 text-gray-500">
                    <Loader2 className="w-10 h-10 animate-spin mb-4 text-blue-500" />
                    <p className="text-lg font-medium text-gray-300">Fetching jobs...</p>
                    <p className="text-sm mt-1">Pulling from Greenhouse, Lever, Amazon, and more</p>
                  </div>
                )}

                {isError && (
                  <div className="card border-red-800 p-6 text-center">
                    <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-3" />
                    <p className="text-red-300 font-medium">Failed to load jobs</p>
                    <p className="text-gray-500 text-sm mt-1">
                      Make sure the backend is running on port 8000.
                      <br />Then click <strong>Refresh Jobs</strong>.
                    </p>
                    <p className="text-xs text-gray-600 mt-2 font-mono">{error?.message}</p>
                  </div>
                )}

                {!isLoading && !isError && displayJobs.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-24 text-gray-500">
                    <LayoutGrid className="w-12 h-12 mb-4 opacity-30" />
                    <p className="text-lg font-medium text-gray-300">No jobs found</p>
                    <p className="text-sm mt-1">Try clicking <strong>Refresh Jobs</strong> to fetch fresh postings</p>
                  </div>
                )}

                {!isLoading && displayJobs.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-gray-400">
                        {displayJobs.length} jobs · sorted by AI match score
                      </p>
                    </div>
                    {displayJobs.map(job => (
                      <JobCard key={job.id} job={job} onSelect={setSelectedJob} />
                    ))}
                  </div>
                )}
              </main>
            </div>
          </>
        )}
      </div>

      {showProfile && (
        <ProfileSetup
          onSave={handleProfileSave}
          onClose={() => setShowProfile(false)}
        />
      )}

      {selectedJob && (
        <JobDetailModal
          job={selectedJob}
          onClose={() => setSelectedJob(null)}
        />
      )}
    </div>
  )
}
