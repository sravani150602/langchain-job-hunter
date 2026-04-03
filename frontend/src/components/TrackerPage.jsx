import { useState } from 'react'
import { Trash2, ExternalLink, ChevronDown, Loader2, BarChart3, CheckCircle, XCircle, Clock, Star, BookOpen } from 'lucide-react'
import { useTracker, useTrackerStats, useUpdateApplication, useDeleteApplication } from '../hooks/useJobs.js'
import clsx from 'clsx'

const STATUS_CONFIG = {
  saved:       { label: 'Saved',       color: 'bg-gray-800 text-gray-300 border-gray-700',   dot: 'bg-gray-400' },
  applied:     { label: 'Applied',     color: 'bg-blue-900/40 text-blue-300 border-blue-800', dot: 'bg-blue-400' },
  interviewing:{ label: 'Interviewing',color: 'bg-yellow-900/30 text-yellow-300 border-yellow-800', dot: 'bg-yellow-400' },
  offer:       { label: 'Offer!',      color: 'bg-green-900/30 text-green-300 border-green-800', dot: 'bg-green-400' },
  rejected:    { label: 'Rejected',    color: 'bg-red-900/20 text-red-400 border-red-900',    dot: 'bg-red-500' },
}

const STATUSES = Object.keys(STATUS_CONFIG)

function StatusPill({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.saved
  return (
    <span className={clsx('inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full border', cfg.color)}>
      <span className={clsx('w-1.5 h-1.5 rounded-full', cfg.dot)} />
      {cfg.label}
    </span>
  )
}

function StatCard({ label, value, icon: Icon, color }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center gap-3">
      <div className={clsx('w-10 h-10 rounded-lg flex items-center justify-center', color)}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <div className="text-2xl font-bold text-white">{value}</div>
        <div className="text-xs text-gray-500">{label}</div>
      </div>
    </div>
  )
}

function ApplicationRow({ entry }) {
  const { mutate: update, isPending: isUpdating } = useUpdateApplication()
  const { mutate: del, isPending: isDeleting } = useDeleteApplication()
  const [showNotes, setShowNotes] = useState(false)
  const [notesText, setNotesText] = useState(entry.notes || '')

  const handleStatusChange = (status) => {
    update({ id: entry.id, status })
  }

  const handleNotesSave = () => {
    update({ id: entry.id, notes: notesText })
    setShowNotes(false)
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-white text-sm">{entry.job_title}</h3>
          <p className="text-blue-400 text-xs">{entry.company}</p>
          {entry.location && <p className="text-gray-500 text-xs mt-0.5">{entry.location}</p>}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <StatusPill status={entry.status} />
          {entry.url && (
            <a href={entry.url} target="_blank" rel="noopener noreferrer"
               className="text-gray-500 hover:text-gray-300">
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>

      {/* Status change buttons */}
      <div className="flex flex-wrap gap-1.5 mt-3">
        {STATUSES.map(s => (
          <button
            key={s}
            onClick={() => handleStatusChange(s)}
            disabled={entry.status === s || isUpdating}
            className={clsx(
              'text-xs px-2.5 py-1 rounded-full border transition-colors',
              entry.status === s
                ? 'opacity-50 cursor-not-allowed ' + STATUS_CONFIG[s].color
                : 'border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-200'
            )}
          >
            {STATUS_CONFIG[s].label}
          </button>
        ))}
      </div>

      {/* Notes section */}
      <div className="mt-2">
        <button
          onClick={() => setShowNotes(!showNotes)}
          className="text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1"
        >
          <ChevronDown className={clsx('w-3 h-3 transition-transform', showNotes && 'rotate-180')} />
          {entry.notes ? 'Edit notes' : 'Add notes'}
        </button>
        {showNotes && (
          <div className="mt-2">
            <textarea
              rows={2}
              value={notesText}
              onChange={e => setNotesText(e.target.value)}
              placeholder="Notes about this application..."
              className="input text-xs resize-none w-full"
            />
            <button onClick={handleNotesSave} className="btn-primary text-xs mt-2 px-3 py-1.5">
              Save
            </button>
          </div>
        )}
        {!showNotes && entry.notes && (
          <p className="text-xs text-gray-500 mt-1 italic">{entry.notes}</p>
        )}
      </div>

      {/* Delete */}
      <div className="mt-2 flex justify-end">
        <button
          onClick={() => del(entry.id)}
          disabled={isDeleting}
          className="text-xs text-gray-600 hover:text-red-400 flex items-center gap-1 transition-colors"
        >
          <Trash2 className="w-3 h-3" />
          Remove
        </button>
      </div>
    </div>
  )
}

export default function TrackerPage() {
  const { data: applications = [], isLoading } = useTracker()
  const { data: stats } = useTrackerStats()

  if (isLoading) {
    return (
      <div className="flex flex-col items-center py-24 text-gray-500">
        <Loader2 className="w-8 h-8 animate-spin text-blue-400 mb-3" />
        Loading applications...
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <StatCard label="Total" value={stats.total} icon={BarChart3} color="bg-blue-900/40 text-blue-400" />
          <StatCard label="Applied" value={stats.by_status.applied || 0} icon={CheckCircle} color="bg-blue-900/40 text-blue-400" />
          <StatCard label="Interviewing" value={stats.by_status.interviewing || 0} icon={BookOpen} color="bg-yellow-900/30 text-yellow-400" />
          <StatCard label="Offers" value={stats.by_status.offer || 0} icon={Star} color="bg-green-900/30 text-green-400" />
          <StatCard label="Rejected" value={stats.by_status.rejected || 0} icon={XCircle} color="bg-red-900/20 text-red-400" />
        </div>
      )}

      {/* Pipeline visual */}
      {stats && stats.total > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-3">Application Pipeline</h3>
          <div className="flex items-center gap-2 text-xs">
            {STATUSES.map((s, i) => (
              <div key={s} className="flex items-center gap-2">
                <div className="text-center">
                  <div className={clsx('text-lg font-bold', {
                    'text-gray-300': s === 'saved',
                    'text-blue-400': s === 'applied',
                    'text-yellow-400': s === 'interviewing',
                    'text-green-400': s === 'offer',
                    'text-red-400': s === 'rejected',
                  })}>
                    {stats.by_status[s] || 0}
                  </div>
                  <div className="text-gray-500">{STATUS_CONFIG[s].label}</div>
                </div>
                {i < STATUSES.length - 1 && <span className="text-gray-700">→</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Applications list */}
      {applications.length === 0 ? (
        <div className="flex flex-col items-center py-20 text-gray-500">
          <Clock className="w-12 h-12 mb-4 opacity-30" />
          <p className="text-lg font-medium text-gray-400">No applications tracked yet</p>
          <p className="text-sm mt-1">Click <strong>"Save to Tracker"</strong> on any job to start tracking</p>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-gray-400">{applications.length} application{applications.length !== 1 ? 's' : ''}</p>
          {applications.map(entry => (
            <ApplicationRow key={entry.id} entry={entry} />
          ))}
        </div>
      )}
    </div>
  )
}
