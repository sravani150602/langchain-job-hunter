import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'

// ── Jobs ─────────────────────────────────────────────────────
export function useJobs(filters) {
  const params = new URLSearchParams()
  if (filters.max_hours_ago) params.set('max_hours_ago', filters.max_hours_ago)
  if (filters.job_type)      params.set('job_type', filters.job_type)
  if (filters.priority_only) params.set('priority_only', true)
  if (filters.remote_only)   params.set('remote_only', true)
  if (filters.min_score)     params.set('min_score', filters.min_score)
  params.set('limit', 200)

  return useQuery({
    queryKey: ['jobs', filters],
    queryFn: async () => {
      const { data } = await axios.get(`/api/jobs/?${params}`)
      return data
    },
    refetchInterval: 1000 * 60 * 5,
  })
}

export function useStatus() {
  return useQuery({
    queryKey: ['status'],
    queryFn: async () => {
      const { data } = await axios.get('/api/jobs/status')
      return data
    },
    refetchInterval: 1000 * 30,
  })
}

// ── Resume ────────────────────────────────────────────────────
export function useResume() {
  return useQuery({
    queryKey: ['resume'],
    queryFn: async () => {
      const { data } = await axios.get('/api/resume/')
      return data
    },
  })
}

export function useUploadResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (file) => {
      const formData = new FormData()
      formData.append('file', file)
      const { data } = await axios.post('/api/resume/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resume'] }),
  })
}

export function useAnalyzeJob(jobId, enabled = true) {
  return useQuery({
    queryKey: ['analyze', jobId],
    queryFn: async () => {
      const { data } = await axios.get(`/api/resume/analyze/${jobId}`)
      return data
    },
    enabled: !!jobId && enabled,
    staleTime: 1000 * 60 * 5,
  })
}

export function useOptimizeResume(jobId) {
  return useQuery({
    queryKey: ['optimize', jobId],
    queryFn: async () => {
      const { data } = await axios.get(`/api/resume/optimize/${jobId}`)
      return data
    },
    enabled: false,
    staleTime: 1000 * 60 * 10,
  })
}

export function useInterviewPrep(jobId) {
  return useQuery({
    queryKey: ['interview', jobId],
    queryFn: async () => {
      const { data } = await axios.get(`/api/resume/interview/${jobId}`)
      return data
    },
    enabled: false,
    staleTime: 1000 * 60 * 10,
  })
}

// ── Tracker ───────────────────────────────────────────────────
export function useTracker() {
  return useQuery({
    queryKey: ['tracker'],
    queryFn: async () => {
      const { data } = await axios.get('/api/tracker/')
      return data
    },
  })
}

export function useTrackerStats() {
  return useQuery({
    queryKey: ['trackerStats'],
    queryFn: async () => {
      const { data } = await axios.get('/api/tracker/stats')
      return data
    },
  })
}

export function useAddApplication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (entry) => {
      const { data } = await axios.post('/api/tracker/', entry)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tracker'] })
      qc.invalidateQueries({ queryKey: ['trackerStats'] })
    },
  })
}

export function useUpdateApplication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...update }) => {
      const { data } = await axios.patch(`/api/tracker/${id}`, update)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tracker'] })
      qc.invalidateQueries({ queryKey: ['trackerStats'] })
    },
  })
}

export function useDeleteApplication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id) => {
      await axios.delete(`/api/tracker/${id}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tracker'] })
      qc.invalidateQueries({ queryKey: ['trackerStats'] })
    },
  })
}
