import { ExternalLink, MapPin, Clock, Users, Zap, ChevronDown, ChevronUp, Sparkles } from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'

function ScoreRing({ score }) {
  if (score == null) return null
  const cls = score >= 80 ? 'score-excellent'
            : score >= 60 ? 'score-good'
            : score >= 40 ? 'score-ok'
            : 'score-poor'
  return (
    <div className={clsx('score-ring', cls)}>
      {score}
    </div>
  )
}

function SourceBadge({ source }) {
  const map = {
    greenhouse: ['tag-green', 'Greenhouse'],
    lever:      ['tag-purple', 'Lever'],
    adzuna:     ['tag-blue', 'Adzuna'],
    amazon:     ['tag-orange', 'Amazon Direct'],
  }
  const [cls, label] = map[source] || ['tag-gray', source]
  return <span className={clsx('tag', cls)}>{label}</span>
}

function UrgencyBadge({ urgency }) {
  if (!urgency) return null
  if (urgency === 'apply-now') return (
    <span className="tag bg-green-500/20 text-green-300 border border-green-600 flex items-center gap-1">
      <Zap className="w-3 h-3" /> Apply Now
    </span>
  )
  if (urgency === 'consider') return (
    <span className="tag bg-yellow-900/30 text-yellow-400 border border-yellow-700">Consider</span>
  )
  return null
}

const SOURCE_LABELS = {
  greenhouse: 'Greenhouse',
  lever: 'Lever',
  adzuna: 'Adzuna',
  amazon: 'Amazon',
}

// Company logo placeholder using initials
function CompanyLogo({ company }) {
  const initials = company.split(/[\s(]/)[0].slice(0, 2).toUpperCase()
  const colors = [
    'from-blue-600 to-blue-800',
    'from-purple-600 to-purple-800',
    'from-green-600 to-green-800',
    'from-orange-600 to-orange-800',
    'from-pink-600 to-pink-800',
    'from-cyan-600 to-cyan-800',
  ]
  const color = colors[initials.charCodeAt(0) % colors.length]
  return (
    <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center text-white font-bold text-sm flex-shrink-0`}>
      {initials}
    </div>
  )
}

export default function JobCard({ job, onSelect }) {
  const [expanded, setExpanded] = useState(false)

  const {
    title, company, location, posted_label, hours_ago,
    url, source, is_priority, remote,
    match_score, match_reasons, missing_skills, job_summary,
    requirements, description, applicant_count,
    salary_min, salary_max,
  } = job

  const isNew = hours_ago != null && hours_ago < 6
  const isFresh = hours_ago != null && hours_ago < 24

  return (
    <article className={clsx(
      'card animate-slide-in',
      is_priority && 'border-blue-800/60',
    )}>
      <div className="flex gap-3">
        <CompanyLogo company={company} />

        <div className="flex-1 min-w-0">
          {/* Top row */}
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="font-semibold text-white text-base leading-tight">{title}</h2>
                {isNew && (
                  <span className="tag bg-red-500/20 text-red-300 border border-red-700 text-xs animate-pulse">
                    NEW
                  </span>
                )}
              </div>
              <div className="text-sm text-blue-400 font-medium mt-0.5">{company}</div>
            </div>
            <ScoreRing score={match_score} />
          </div>

          {/* Meta row */}
          <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-gray-400">
            {location && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {location}
              </span>
            )}
            {posted_label && (
              <span className={clsx(
                'flex items-center gap-1',
                isFresh ? 'text-green-400' : 'text-gray-400'
              )}>
                <Clock className="w-3 h-3" />
                {posted_label}
              </span>
            )}
            {applicant_count != null && (
              <span className="flex items-center gap-1">
                <Users className="w-3 h-3" />
                {applicant_count.toLocaleString()} applicants
              </span>
            )}
            {salary_min && salary_max && (
              <span className="text-green-400">
                ${Math.round(salary_min / 1000)}k – ${Math.round(salary_max / 1000)}k
              </span>
            )}
          </div>

          {/* Badges */}
          <div className="flex flex-wrap gap-1.5 mt-2">
            <SourceBadge source={source} />
            {remote && <span className="tag tag-green">Remote</span>}
            {is_priority && <span className="tag tag-orange">Top Company</span>}
          </div>

          {/* AI Summary */}
          {job_summary && (
            <p className="text-sm text-gray-300 mt-2 leading-relaxed">{job_summary}</p>
          )}

          {/* Match reasons */}
          {match_reasons && match_reasons.length > 0 && (
            <div className="mt-2 space-y-0.5">
              {match_reasons.map((r, i) => (
                <div key={i} className="text-xs text-gray-400 flex items-start gap-1.5">
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span>{r}</span>
                </div>
              ))}
            </div>
          )}

          {/* Missing skills */}
          {missing_skills && missing_skills.length > 0 && (
            <div className="mt-1.5 flex flex-wrap gap-1">
              <span className="text-xs text-gray-500">Gap:</span>
              {missing_skills.map((s, i) => (
                <span key={i} className="tag tag-gray">{s}</span>
              ))}
            </div>
          )}

          {/* Expanded: requirements + description */}
          {expanded && (
            <div className="mt-3 border-t border-gray-800 pt-3 space-y-3 animate-slide-in">
              {requirements && requirements.length > 0 && (
                <div>
                  <h3 className="text-xs text-gray-400 uppercase tracking-wider mb-1.5">Requirements</h3>
                  <ul className="space-y-1">
                    {requirements.map((r, i) => (
                      <li key={i} className="text-xs text-gray-300 flex items-start gap-1.5">
                        <span className="text-blue-500 mt-0.5">•</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {description && (
                <div>
                  <h3 className="text-xs text-gray-400 uppercase tracking-wider mb-1.5">Description</h3>
                  <p className="text-xs text-gray-400 leading-relaxed line-clamp-6"
                     dangerouslySetInnerHTML={{ __html: description.replace(/<[^>]+>/g, '') }} />
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2 mt-3">
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary text-xs px-3 py-1.5"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Apply
            </a>
            {onSelect && (
              <button
                onClick={() => onSelect(job)}
                className="btn-secondary text-xs px-3 py-1.5 text-blue-300 border-blue-800"
              >
                <Sparkles className="w-3.5 h-3.5" />
                AI Analyze
              </button>
            )}
            <button
              onClick={() => setExpanded(!expanded)}
              className="btn-secondary text-xs px-3 py-1.5"
            >
              {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              {expanded ? 'Less' : 'Details'}
            </button>
          </div>
        </div>
      </div>
    </article>
  )
}
