export type PreviewRow = Record<string, string | number | null | undefined>

export type ProcessingReport = {
  records_imported?: number
  records_after_doi?: number
  records_after_pmid?: number
  records_after_exact_title?: number
  records_after_fuzzy?: number
  final_records?: number
  removed_by_doi?: number
  removed_by_pmid?: number
  removed_by_exact_title?: number
  removed_by_fuzzy?: number
  records_after_review?: number
  removed_by_reviewer?: number
  review_decisions_saved?: number
  review_unresolved?: number
  fuzzy_threshold?: number
  source_counts?: Record<string, number>
  prisma?: {
    identified?: number
    after_screening?: number
  }
  stages?: Array<{
    name: string
    removed: number
    remaining: number
  }>
}

export type ConvertResponse = {
  job_id: string
  source_type: string
  conversion: string
  records: number
  preview: PreviewRow[]
  download_name: string
  download_url: string
  artifact: {
    artifact_id: string
    filename: string
    download_url: string
    mime_type: string
    size_bytes: number
  }
}

export type ArtifactInfo = {
  artifact_id: string
  filename: string
  download_url: string
  mime_type: string
  size_bytes: number
}

export type DeduplicateResponse = {
  job_id: string
  preview: PreviewRow[]
  master_preview: PreviewRow[]
  review_preview: PreviewRow[]
  report: ProcessingReport
  artifacts: Record<string, ArtifactInfo>
  finalized: boolean
}
