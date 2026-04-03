import { SlidersHorizontal, X } from 'lucide-react'
import { useState } from 'react'

const COMPANIES = [
  'Google', 'Meta', 'Amazon', 'Apple', 'Microsoft', 'Netflix',
  'Nvidia', 'PayPal', 'Uber', 'Stripe', 'Airbnb', 'Databricks',
  'Snowflake', 'Discord', 'Coinbase', 'OpenAI', 'Anthropic'
]

export default function FilterPanel({ filters, onChange }) {
  const [open, setOpen] = useState(true)

  const set = (key, val) => onChange({ ...filters, [key]: val })

  const toggleCompany = (company) => {
    const current = filters.companies || []
    if (current.includes(company)) {
      set('companies', current.filter(c => c !== company))
    } else {
      set('companies', [...current, company])
    }
  }

  return (
    <aside className="w-full lg:w-64 flex-shrink-0">
      <div className="card sticky top-20">
        <div
          className="flex items-center justify-between cursor-pointer mb-3"
          onClick={() => setOpen(!open)}
        >
          <div className="flex items-center gap-2 font-semibold text-white">
            <SlidersHorizontal className="w-4 h-4 text-blue-400" />
            Filters
          </div>
          <span className="text-gray-500 text-xs">{open ? '▲' : '▼'}</span>
        </div>

        {open && (
          <div className="space-y-5 animate-slide-in">
            {/* Role Type */}
            <div>
              <label className="text-xs text-gray-400 uppercase tracking-wider mb-2 block">Role Type</label>
              <div className="space-y-1.5">
                {[
                  ['', 'All Roles'],
                  ['software-engineering', 'Software Engineering'],
                  ['data-engineering', 'Data Engineering'],
                ].map(([val, label]) => (
                  <label key={val} className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="radio"
                      name="job_type"
                      value={val}
                      checked={filters.job_type === val}
                      onChange={() => set('job_type', val)}
                      className="accent-blue-500"
                    />
                    <span className="text-sm text-gray-300 group-hover:text-white transition-colors">{label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Posted Within */}
            <div>
              <label className="text-xs text-gray-400 uppercase tracking-wider mb-2 block">
                Posted Within
              </label>
              <select
                value={filters.max_hours_ago}
                onChange={e => set('max_hours_ago', Number(e.target.value))}
                className="select"
              >
                <option value={6}>Last 6 hours</option>
                <option value={24}>Last 24 hours</option>
                <option value={48}>Last 48 hours</option>
                <option value={72}>Last 3 days</option>
                <option value={168}>Last week</option>
              </select>
            </div>

            {/* Min Match Score */}
            <div>
              <label className="text-xs text-gray-400 uppercase tracking-wider mb-2 block">
                Min AI Match Score: <span className="text-blue-400">{filters.min_score}+</span>
              </label>
              <input
                type="range"
                min={0}
                max={80}
                step={10}
                value={filters.min_score}
                onChange={e => set('min_score', Number(e.target.value))}
                className="w-full accent-blue-500"
              />
              <div className="flex justify-between text-xs text-gray-600 mt-1">
                <span>0</span><span>40</span><span>80</span>
              </div>
            </div>

            {/* Toggles */}
            <div className="space-y-2.5">
              <label className="flex items-center justify-between cursor-pointer">
                <span className="text-sm text-gray-300">FAANG Only</span>
                <button
                  onClick={() => set('priority_only', !filters.priority_only)}
                  className={`w-10 h-5 rounded-full transition-colors ${filters.priority_only ? 'bg-blue-600' : 'bg-gray-700'}`}
                >
                  <div className={`w-4 h-4 bg-white rounded-full mx-0.5 transition-transform ${filters.priority_only ? 'translate-x-5' : 'translate-x-0'}`} />
                </button>
              </label>
              <label className="flex items-center justify-between cursor-pointer">
                <span className="text-sm text-gray-300">Remote Only</span>
                <button
                  onClick={() => set('remote_only', !filters.remote_only)}
                  className={`w-10 h-5 rounded-full transition-colors ${filters.remote_only ? 'bg-blue-600' : 'bg-gray-700'}`}
                >
                  <div className={`w-4 h-4 bg-white rounded-full mx-0.5 transition-transform ${filters.remote_only ? 'translate-x-5' : 'translate-x-0'}`} />
                </button>
              </label>
            </div>

            {/* Company Filter */}
            <div>
              <label className="text-xs text-gray-400 uppercase tracking-wider mb-2 block">Companies</label>
              <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto">
                {COMPANIES.map(company => {
                  const active = (filters.companies || []).includes(company)
                  return (
                    <button
                      key={company}
                      onClick={() => toggleCompany(company)}
                      className={`text-xs px-2 py-1 rounded border transition-colors ${
                        active
                          ? 'bg-blue-600 border-blue-500 text-white'
                          : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500'
                      }`}
                    >
                      {company}
                    </button>
                  )
                })}
              </div>
              {(filters.companies || []).length > 0 && (
                <button
                  onClick={() => set('companies', [])}
                  className="text-xs text-gray-500 hover:text-gray-300 mt-2 flex items-center gap-1"
                >
                  <X className="w-3 h-3" /> Clear companies
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}
