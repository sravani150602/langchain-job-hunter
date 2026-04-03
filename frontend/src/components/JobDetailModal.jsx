import { useState } from 'react'
import { X, ExternalLink, MapPin, Clock, Target, Zap, BookOpen, FileEdit, Loader2, CheckCircle, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import { useAnalyzeJob, useOptimizeResume, useInterviewPrep, useResume, useAddApplication } from '../hooks/useJobs.js'
import clsx from 'clsx'

const TABS = ['Overview', 'AI Analysis', 'Optimize Resume', 'Interview Prep']

function ScoreMeter({ score }) {
  const cls = score >= 80 ? 'text-green-400' : score >= 60 ? 'text-yellow-400' : score >= 40 ? 'text-orange-400' : 'text-red-400'
  const bar = score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-500' : score >= 40 ? 'bg-orange-500' : 'bg-red-500'
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-gray-400">AI Match Score</span>
        <span className={clsx('text-2xl font-bold', cls)}>{score}/100</span>
      </div>
      <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
        <div className={clsx('h-full rounded-full transition-all duration-500', bar)} style={{ width: `${score}%` }} />
      </div>
    </div>
  )
}

function TabContent({ tab, job, analysis, optimization, interviewPrep, onFetchOptimize, onFetchInterview, isOptimizing, isInterviewing }) {
  if (tab === 'Overview') {
    return (
      <div className="space-y-4">
        {job.job_summary && (
          <p className="text-gray-300 text-sm leading-relaxed">{job.job_summary}</p>
        )}
        {job.requirements?.length > 0 && (
          <div>
            <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Requirements</h4>
            <ul className="space-y-1.5">
              {job.requirements.map((r, i) => (
                <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className="text-blue-500 mt-0.5 flex-shrink-0">•</span>
                  {r}
                </li>
              ))}
            </ul>
          </div>
        )}
        {job.description && (
          <div>
            <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Description</h4>
            <p className="text-sm text-gray-400 leading-relaxed whitespace-pre-line line-clamp-10">
              {job.description.replace(/<[^>]+>/g, '')}
            </p>
          </div>
        )}
      </div>
    )
  }

  if (tab === 'AI Analysis') {
    if (!analysis) {
      return (
        <div className="flex flex-col items-center py-12 text-gray-500">
          <Loader2 className="w-8 h-8 animate-spin text-blue-400 mb-3" />
          <p>Analyzing job fit with AI...</p>
        </div>
      )
    }
    return (
      <div className="space-y-5">
        <ScoreMeter score={analysis.score} />

        <div className="flex items-center gap-2">
          {analysis.verdict === 'apply-now' && (
            <span className="flex items-center gap-1.5 text-green-400 bg-green-900/20 border border-green-800 rounded-full px-3 py-1 text-sm font-medium">
              <Zap className="w-3.5 h-3.5" /> Apply Now
            </span>
          )}
          {analysis.verdict === 'consider' && (
            <span className="text-yellow-400 bg-yellow-900/20 border border-yellow-800 rounded-full px-3 py-1 text-sm font-medium">
              Worth Considering
            </span>
          )}
          {analysis.verdict === 'skip' && (
            <span className="text-gray-400 bg-gray-800 border border-gray-700 rounded-full px-3 py-1 text-sm">
              Weak Match
            </span>
          )}
        </div>

        {analysis.matched_skills?.length > 0 && (
          <div>
            <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5 text-green-500" /> Matched Skills
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {analysis.matched_skills.map((s, i) => (
                <span key={i} className="tag bg-green-900/30 text-green-300 border border-green-800">{s}</span>
              ))}
            </div>
          </div>
        )}

        {analysis.missing_skills?.length > 0 && (
          <div>
            <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5 text-orange-400" /> Skills Gap
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {analysis.missing_skills.map((s, i) => (
                <span key={i} className="tag bg-orange-900/20 text-orange-300 border border-orange-800">{s}</span>
              ))}
            </div>
          </div>
        )}

        {analysis.strengths?.length > 0 && (
          <div>
            <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Why You're a Fit</h4>
            <ul className="space-y-1">
              {analysis.strengths.map((r, i) => (
                <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span> {r}
                </li>
              ))}
            </ul>
          </div>
        )}

        {analysis.recommendations?.length > 0 && (
          <div>
            <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Recommendations</h4>
            <ul className="space-y-1">
              {analysis.recommendations.map((r, i) => (
                <li key={i} className="text-sm text-blue-300 flex items-start gap-2">
                  <span className="text-blue-500 mt-0.5">→</span> {r}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    )
  }

  if (tab === 'Optimize Resume') {
    if (!optimization && !isOptimizing) {
      return (
        <div className="flex flex-col items-center py-12 text-gray-500 gap-4">
          <FileEdit className="w-12 h-12 opacity-30" />
          <p className="text-gray-400 font-medium">Get AI-powered resume suggestions</p>
          <p className="text-sm text-center">We'll rewrite your bullets and highlight the right keywords for this specific role.</p>
          <button onClick={onFetchOptimize} className="btn-primary">
            Generate Optimization
          </button>
        </div>
      )
    }
    if (isOptimizing) {
      return (
        <div className="flex flex-col items-center py-12 text-gray-500">
          <Loader2 className="w-8 h-8 animate-spin text-blue-400 mb-3" />
          <p>Generating resume optimizations...</p>
        </div>
      )
    }
    return (
      <div className="space-y-5">
        {optimization.summary_rewrite && (
          <div>
            <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Tailored Summary</h4>
            <p className="text-sm text-gray-300 bg-blue-900/20 border border-blue-800 rounded-lg p-3 leading-relaxed italic">
              "{optimization.summary_rewrite}"
            </p>
          </div>
        )}

        {optimization.keywords_to_add?.length > 0 && (
          <div>
            <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Keywords to Add</h4>
            <div className="flex flex-wrap gap-1.5">
              {optimization.keywords_to_add.map((k, i) => (
                <span key={i} className="tag bg-purple-900/30 text-purple-300 border border-purple-800">{k}</span>
              ))}
            </div>
          </div>
        )}

        {optimization.skills_to_highlight?.length > 0 && (
          <div>
            <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Highlight These Skills</h4>
            <div className="flex flex-wrap gap-1.5">
              {optimization.skills_to_highlight.map((s, i) => (
                <span key={i} className="tag bg-green-900/30 text-green-300 border border-green-800">{s}</span>
              ))}
            </div>
          </div>
        )}

        {optimization.optimized_bullets?.length > 0 && (
          <div>
            <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Improved Bullet Points</h4>
            <div className="space-y-3">
              {optimization.optimized_bullets.map((b, i) => (
                <div key={i} className="border border-gray-800 rounded-lg p-3 space-y-2">
                  <div className="flex items-start gap-2">
                    <span className="text-xs text-red-400 mt-0.5 flex-shrink-0">Before:</span>
                    <p className="text-xs text-gray-500 line-through">{b.original}</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-xs text-green-400 mt-0.5 flex-shrink-0">After:</span>
                    <p className="text-xs text-green-300">{b.improved}</p>
                  </div>
                  <p className="text-xs text-gray-600 italic">{b.reason}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  if (tab === 'Interview Prep') {
    if (!interviewPrep && !isInterviewing) {
      return (
        <div className="flex flex-col items-center py-12 text-gray-500 gap-4">
          <BookOpen className="w-12 h-12 opacity-30" />
          <p className="text-gray-400 font-medium">Prepare for your interview</p>
          <p className="text-sm text-center">Get behavioral, technical, and company-specific questions tailored to this role.</p>
          <button onClick={onFetchInterview} className="btn-primary">
            Generate Questions
          </button>
        </div>
      )
    }
    if (isInterviewing) {
      return (
        <div className="flex flex-col items-center py-12 text-gray-500">
          <Loader2 className="w-8 h-8 animate-spin text-blue-400 mb-3" />
          <p>Generating interview questions...</p>
        </div>
      )
    }

    const QGroup = ({ title, questions, color }) => (
      questions?.length > 0 ? (
        <div>
          <h4 className={clsx('text-xs uppercase tracking-wider mb-2 font-semibold', color)}>{title}</h4>
          <div className="space-y-3">
            {questions.map((q, i) => (
              <div key={i} className="border border-gray-800 rounded-lg p-3">
                <p className="text-sm text-white font-medium">{q.question}</p>
                {q.hint && <p className="text-xs text-gray-500 mt-1 italic">Hint: {q.hint}</p>}
              </div>
            ))}
          </div>
        </div>
      ) : null
    )

    return (
      <div className="space-y-5">
        <QGroup title="Behavioral Questions" questions={interviewPrep.behavioral} color="text-blue-400" />
        <QGroup title="Technical Questions" questions={interviewPrep.technical} color="text-purple-400" />
        <QGroup title="Company-Specific Questions" questions={interviewPrep.company_specific} color="text-orange-400" />

        {interviewPrep.topics_to_study?.length > 0 && (
          <div>
            <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Topics to Study</h4>
            <div className="flex flex-wrap gap-1.5">
              {interviewPrep.topics_to_study.map((t, i) => (
                <span key={i} className="tag bg-gray-800 text-gray-300 border border-gray-700">{t}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  return null
}

export default function JobDetailModal({ job, onClose }) {
  const [activeTab, setActiveTab] = useState('Overview')
  const { data: resume } = useResume()
  const { data: analysis, isLoading: isAnalyzing } = useAnalyzeJob(job.id, !!resume)
  const { data: optimization, isFetching: isOptimizing, refetch: fetchOptimize } = useOptimizeResume(job.id)
  const { data: interviewPrep, isFetching: isInterviewing, refetch: fetchInterview } = useInterviewPrep(job.id)
  const { mutate: addApplication, isPending: isSaving } = useAddApplication()
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    addApplication({
      id: '',
      job_id: job.id,
      job_title: job.title,
      company: job.company,
      location: job.location || '',
      url: job.url || '',
      status: 'saved',
    }, {
      onSuccess: () => setSaved(true),
    })
  }

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-start justify-center p-4 overflow-y-auto">
      <div className="bg-gray-950 border border-gray-800 rounded-2xl w-full max-w-2xl my-8 shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-gray-950 border-b border-gray-800 px-5 py-4 flex items-start justify-between gap-3 rounded-t-2xl">
          <div>
            <h2 className="font-bold text-white text-lg leading-tight">{job.title}</h2>
            <p className="text-blue-400 text-sm font-medium">{job.company}</p>
            <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
              {job.location && <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{job.location}</span>}
              {job.posted_label && <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{job.posted_label}</span>}
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white mt-1 flex-shrink-0">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Actions */}
        <div className="px-5 py-3 flex gap-2 flex-wrap border-b border-gray-900">
          <a href={job.url} target="_blank" rel="noopener noreferrer" className="btn-primary text-xs px-3 py-1.5">
            <ExternalLink className="w-3.5 h-3.5" /> Apply Now
          </a>
          <button
            onClick={handleSave}
            disabled={saved || isSaving}
            className={clsx(
              'btn-secondary text-xs px-3 py-1.5',
              saved && 'opacity-50 cursor-not-allowed'
            )}
          >
            {saved ? <><CheckCircle className="w-3.5 h-3.5 text-green-400" /> Saved</> : <><Target className="w-3.5 h-3.5" /> Save to Tracker</>}
          </button>
        </div>

        {/* No resume warning */}
        {!resume && (
          <div className="mx-5 mt-4 flex items-center gap-2 text-yellow-400 bg-yellow-900/20 border border-yellow-800 rounded-xl p-3 text-sm">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            Upload your resume to unlock AI analysis, optimization, and interview prep.
          </div>
        )}

        {/* Tabs */}
        <div className="px-5 pt-4">
          <div className="flex gap-1 border-b border-gray-800 pb-0">
            {TABS.map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={clsx(
                  'px-3 py-2 text-xs font-medium rounded-t-lg transition-colors whitespace-nowrap',
                  activeTab === tab
                    ? 'bg-blue-900/30 text-blue-300 border-b-2 border-blue-500'
                    : 'text-gray-500 hover:text-gray-300'
                )}
              >
                {tab}
                {tab === 'AI Analysis' && isAnalyzing && (
                  <Loader2 className="inline w-3 h-3 ml-1 animate-spin" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Tab content */}
        <div className="p-5 max-h-[60vh] overflow-y-auto">
          <TabContent
            tab={activeTab}
            job={job}
            analysis={analysis}
            optimization={optimization}
            interviewPrep={interviewPrep}
            onFetchOptimize={() => fetchOptimize()}
            onFetchInterview={() => fetchInterview()}
            isOptimizing={isOptimizing}
            isInterviewing={isInterviewing}
          />
        </div>
      </div>
    </div>
  )
}
