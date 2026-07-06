import type { ConvertResponse, DeduplicateResponse, PreviewRow } from '../types'

const API_BASE =
  import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const API_PREFIX = `${API_BASE}/api/literature`

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const detail = payload?.detail
    if (Array.isArray(detail)) {
      throw new Error(detail.map((item) => item?.msg ?? String(item)).join('; '))
    }
    throw new Error(typeof detail === 'string' ? detail : response.statusText)
  }
  return response.json() as Promise<T>
}

export async function convertFile(file: File, conversion: string, artifactLifetimeMinutes: number): Promise<ConvertResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('conversion', conversion)
  formData.append('artifact_lifetime_minutes', String(artifactLifetimeMinutes))
  const response = await fetch(`${API_PREFIX}/convert`, {
    method: 'POST',
    body: formData,
  })
  return parseResponse<ConvertResponse>(response)
}

export async function deduplicateFiles(files: File[], artifactLifetimeMinutes: number, fuzzyThreshold: number): Promise<DeduplicateResponse> {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  formData.append('artifact_lifetime_minutes', String(artifactLifetimeMinutes))
  formData.append('fuzzy_threshold', String(fuzzyThreshold))
  const response = await fetch(`${API_PREFIX}/deduplicate`, {
    method: 'POST',
    body: formData,
  })
  return parseResponse<DeduplicateResponse>(response)
}

export async function saveReviewDecisions(jobId: string, decisions: Record<string, string>): Promise<{ job_id: string; saved: boolean; review_preview: PreviewRow[] }> {
  const response = await fetch(`${API_PREFIX}/jobs/${jobId}/review`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ decisions }),
  })
  return parseResponse<{ job_id: string; saved: boolean; review_preview: PreviewRow[] }>(response)
}

export async function finalizeReview(jobId: string, decisions: Record<string, string>): Promise<DeduplicateResponse> {
  const response = await fetch(`${API_PREFIX}/jobs/${jobId}/finalize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ decisions }),
  })
  return parseResponse<DeduplicateResponse>(response)
}

export async function updateFuzzyThreshold(jobId: string, fuzzyThreshold: number): Promise<DeduplicateResponse> {
  const response = await fetch(`${API_PREFIX}/jobs/${jobId}/fuzzy-threshold`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ fuzzy_threshold: fuzzyThreshold }),
  })
  return parseResponse<DeduplicateResponse>(response)
}

export function downloadUrl(jobId: string, artifactId: string): string {
  return `${API_PREFIX}/download/${jobId}/${artifactId}`
}
