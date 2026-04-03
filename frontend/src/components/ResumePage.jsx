import { useState, useRef } from 'react'
import { Upload, FileText, User, Briefcase, GraduationCap, Code, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { useResume, useUploadResume } from '../hooks/useJobs.js'
import clsx from 'clsx'

function SkillBadge({ skill }) {
  return (
    <span className="inline-block px-2 py-0.5 text-xs rounded-full bg-blue-900/40 text-blue-300 border border-blue-800">
      {skill}
    </span>
  )
}

function Section({ icon: Icon, title, children }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4 h-4 text-blue-400" />
        <h3 className="font-semibold text-white text-sm uppercase tracking-wider">{title}</h3>
      </div>
      {children}
    </div>
  )
}

export default function ResumePage() {
  const { data: resume, isLoading } = useResume()
  const { mutateAsync: uploadResume, isPending, error } = useUploadResume()
  const [dragOver, setDragOver] = useState(false)
  const [uploadedName, setUploadedName] = useState(null)
  const fileRef = useRef()

  const handleFile = async (file) => {
    if (!file) return
    if (!file.name.match(/\.(pdf|docx|doc)$/i)) {
      alert('Only PDF and DOCX files are supported.')
      return
    }
    setUploadedName(file.name)
    try {
      await uploadResume(file)
    } catch (e) {
      console.error(e)
    }
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    handleFile(e.dataTransfer.files[0])
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Upload zone */}
      <div
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onClick={() => fileRef.current?.click()}
        className={clsx(
          'border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all',
          dragOver ? 'border-blue-500 bg-blue-900/20' : 'border-gray-700 hover:border-gray-500 bg-gray-900/50'
        )}
      >
        <input
          ref={fileRef}
          type="file"
          className="hidden"
          accept=".pdf,.doc,.docx"
          onChange={e => handleFile(e.target.files[0])}
        />
        {isPending ? (
          <div className="flex flex-col items-center gap-3 text-gray-400">
            <Loader2 className="w-10 h-10 animate-spin text-blue-400" />
            <p className="font-medium text-white">Parsing resume with AI...</p>
            <p className="text-sm">Extracting skills, experience, and education</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 text-gray-400">
            <Upload className="w-10 h-10 text-gray-500" />
            <p className="font-medium text-white text-lg">
              {resume ? 'Replace Resume' : 'Upload Your Resume'}
            </p>
            <p className="text-sm">Drag and drop or click to select · PDF or DOCX · Max 10 MB</p>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-400 bg-red-900/20 border border-red-800 rounded-xl p-3 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error?.response?.data?.detail || 'Upload failed. Please try again.'}
        </div>
      )}

      {uploadedName && !isPending && resume && (
        <div className="flex items-center gap-2 text-green-400 bg-green-900/20 border border-green-800 rounded-xl p-3 text-sm">
          <CheckCircle className="w-4 h-4" />
          Resume parsed successfully: <span className="font-medium">{uploadedName}</span>
        </div>
      )}

      {/* Parsed resume display */}
      {isLoading && (
        <div className="text-center py-12 text-gray-500">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-blue-400" />
          Loading resume...
        </div>
      )}

      {!isLoading && resume && (
        <div className="space-y-4">
          {/* Header */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-start gap-4">
              <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-600 to-purple-700 flex items-center justify-center text-white font-bold text-xl flex-shrink-0">
                {resume.name ? resume.name.slice(0, 2).toUpperCase() : '?'}
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">{resume.name || 'Your Name'}</h2>
                <p className="text-blue-400 text-sm font-medium">{resume.target_role || 'Software Engineer'}</p>
                <div className="flex gap-3 mt-1 text-xs text-gray-400">
                  {resume.email && <span>{resume.email}</span>}
                  {resume.phone && <span>{resume.phone}</span>}
                </div>
                {resume.summary && (
                  <p className="text-gray-300 text-sm mt-2 leading-relaxed">{resume.summary}</p>
                )}
              </div>
            </div>
          </div>

          {/* Skills */}
          {resume.skills?.length > 0 && (
            <Section icon={Code} title={`Skills (${resume.skills.length})`}>
              <div className="flex flex-wrap gap-1.5">
                {resume.skills.map((s, i) => <SkillBadge key={i} skill={s} />)}
              </div>
            </Section>
          )}

          {/* Experience */}
          {resume.experience?.length > 0 && (
            <Section icon={Briefcase} title="Experience">
              <div className="space-y-4">
                {resume.experience.map((exp, i) => (
                  <div key={i} className={clsx(i > 0 && 'border-t border-gray-800 pt-4')}>
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-semibold text-white text-sm">{exp.title}</p>
                        <p className="text-blue-400 text-xs">{exp.company}</p>
                      </div>
                      <span className="text-xs text-gray-500">{exp.duration}</span>
                    </div>
                    {exp.bullets?.length > 0 && (
                      <ul className="mt-2 space-y-1">
                        {exp.bullets.map((b, j) => (
                          <li key={j} className="text-xs text-gray-300 flex items-start gap-1.5">
                            <span className="text-blue-500 mt-0.5">•</span>
                            {b}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Education */}
          {resume.education?.length > 0 && (
            <Section icon={GraduationCap} title="Education">
              <div className="space-y-2">
                {resume.education.map((edu, i) => (
                  <div key={i} className="flex justify-between items-start">
                    <div>
                      <p className="font-semibold text-white text-sm">{edu.degree}</p>
                      <p className="text-blue-400 text-xs">{edu.institution}</p>
                      {edu.gpa && <p className="text-gray-500 text-xs">GPA: {edu.gpa}</p>}
                    </div>
                    <span className="text-xs text-gray-500">{edu.year}</span>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Projects */}
          {resume.projects?.length > 0 && (
            <Section icon={Code} title="Projects">
              <div className="space-y-3">
                {resume.projects.map((proj, i) => (
                  <div key={i} className={clsx(i > 0 && 'border-t border-gray-800 pt-3')}>
                    <p className="font-semibold text-white text-sm">{proj.name}</p>
                    {proj.description && (
                      <p className="text-gray-400 text-xs mt-1">{proj.description}</p>
                    )}
                    {proj.technologies?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {proj.technologies.map((t, j) => <SkillBadge key={j} skill={t} />)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}
        </div>
      )}

      {!isLoading && !resume && (
        <div className="text-center py-16 text-gray-500">
          <FileText className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium text-gray-400">No resume uploaded yet</p>
          <p className="text-sm mt-1">Upload your PDF or DOCX resume above to get started</p>
        </div>
      )}
    </div>
  )
}
