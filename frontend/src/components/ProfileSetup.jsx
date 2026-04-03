import { useState } from 'react'
import { User, X, Save } from 'lucide-react'

const DEFAULT_PROFILE = {
  skills: ['Python', 'Java', 'SQL', 'AWS', 'Docker', 'React', 'LangChain', 'Git'],
  yoe: 0,
  education: 'BS Computer Science',
  preferred_roles: ['Software Engineer', 'Data Engineer'],
  preferred_locations: ['Remote', 'San Francisco', 'New York', 'Seattle'],
  remote_only: false,
  resume_summary: '',
}

export default function ProfileSetup({ onSave, onClose }) {
  const stored = localStorage.getItem('user_profile')
  const [profile, setProfile] = useState(stored ? JSON.parse(stored) : DEFAULT_PROFILE)
  const [skillInput, setSkillInput] = useState('')

  const set = (key, val) => setProfile(p => ({ ...p, [key]: val }))

  const addSkill = () => {
    const s = skillInput.trim()
    if (s && !profile.skills.includes(s)) {
      set('skills', [...profile.skills, s])
      setSkillInput('')
    }
  }

  const removeSkill = (skill) => set('skills', profile.skills.filter(s => s !== skill))

  const handleSave = () => {
    localStorage.setItem('user_profile', JSON.stringify(profile))
    onSave(profile)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="sticky top-0 bg-gray-900 border-b border-gray-800 px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <User className="w-5 h-5 text-blue-400" />
            <h2 className="font-bold text-white text-lg">Your Profile</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-5">
          {/* YOE */}
          <div>
            <label className="block text-sm text-gray-300 mb-1.5 font-medium">
              Years of Experience <span className="text-gray-500">(0 = fresh grad)</span>
            </label>
            <input
              type="number"
              min={0}
              max={30}
              step={0.5}
              value={profile.yoe}
              onChange={e => set('yoe', parseFloat(e.target.value) || 0)}
              className="input"
            />
          </div>

          {/* Education */}
          <div>
            <label className="block text-sm text-gray-300 mb-1.5 font-medium">Education</label>
            <input
              type="text"
              value={profile.education}
              onChange={e => set('education', e.target.value)}
              placeholder="e.g. BS Computer Science, Georgia Tech"
              className="input"
            />
          </div>

          {/* Skills */}
          <div>
            <label className="block text-sm text-gray-300 mb-1.5 font-medium">Your Skills</label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={skillInput}
                onChange={e => setSkillInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && addSkill()}
                placeholder="Add a skill (press Enter)"
                className="input"
              />
              <button onClick={addSkill} className="btn-secondary whitespace-nowrap">Add</button>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {profile.skills.map(skill => (
                <button
                  key={skill}
                  onClick={() => removeSkill(skill)}
                  className="tag tag-blue flex items-center gap-1 hover:bg-red-900/50 hover:text-red-300 hover:border-red-700 transition-colors"
                >
                  {skill}
                  <X className="w-3 h-3" />
                </button>
              ))}
            </div>
          </div>

          {/* Preferred Roles */}
          <div>
            <label className="block text-sm text-gray-300 mb-1.5 font-medium">Preferred Roles</label>
            <div className="space-y-1.5">
              {['Software Engineer', 'Data Engineer', 'Backend Engineer', 'Frontend Engineer', 'ML Engineer', 'SRE'].map(role => (
                <label key={role} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={profile.preferred_roles.includes(role)}
                    onChange={() => {
                      const roles = profile.preferred_roles.includes(role)
                        ? profile.preferred_roles.filter(r => r !== role)
                        : [...profile.preferred_roles, role]
                      set('preferred_roles', roles)
                    }}
                    className="accent-blue-500 w-4 h-4"
                  />
                  <span className="text-sm text-gray-300">{role}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Remote */}
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={profile.remote_only}
              onChange={e => set('remote_only', e.target.checked)}
              className="accent-blue-500 w-4 h-4"
            />
            <span className="text-sm text-gray-300">Remote jobs only</span>
          </label>

          {/* Resume Summary */}
          <div>
            <label className="block text-sm text-gray-300 mb-1.5 font-medium">
              Resume Summary <span className="text-gray-500">(helps AI match better)</span>
            </label>
            <textarea
              rows={3}
              value={profile.resume_summary}
              onChange={e => set('resume_summary', e.target.value)}
              placeholder="e.g. CS junior at Georgia Tech. Built 3 projects in Python/React. Did internship at startup. Looking for SWE or data roles at big tech."
              className="input resize-none"
            />
          </div>
        </div>

        <div className="sticky bottom-0 bg-gray-900 border-t border-gray-800 px-5 py-4">
          <button onClick={handleSave} className="btn-primary w-full justify-center">
            <Save className="w-4 h-4" />
            Save & Re-score Jobs
          </button>
        </div>
      </div>
    </div>
  )
}
