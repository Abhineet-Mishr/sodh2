import { useState } from 'react'
import { convertFile, deduplicateFiles, finalizeReview, saveReviewDecisions, updateFuzzyThreshold } from '../lib/literature_api'
import type { ConvertResponse, DeduplicateResponse, PreviewRow, ProcessingReport } from '../types/literature'

const conversionOptions = [
  { value: 'RIS_TO_CSV', label: 'RIS -> CSV' },
  { value: 'NBIB_TO_CSV', label: 'NBIB -> CSV' },
  { value: 'CSV_TO_RIS', label: 'CSV -> RIS' },
  { value: 'CSV_TO_NBIB', label: 'CSV -> NBIB' },
]

const artifactLifetimeOptions = [
  { value: 30, label: '30 min' },
  { value: 60, label: '1 hr' },
  { value: 120, label: '2 hr' },
  { value: 180, label: '3 hr' },
  { value: 360, label: '6 hr' },
  { value: 720, label: '12 hr' },
  { value: 1440, label: '24 hr' },
]

const sensitivityModes = [
  { value: 'conservative', label: 'Conservative (98%)', threshold: 98 },
  { value: 'balanced', label: 'Balanced (95%)', threshold: 95 },
  { value: 'aggressive', label: 'Aggressive (90%)', threshold: 90 },
  { value: 'custom', label: 'Custom', threshold: 90 },
] as const

type TabKey = 'convert' | 'dedupe'
type SensitivityMode = (typeof sensitivityModes)[number]['value']

function thresholdForMode(mode: SensitivityMode, customThreshold: number) {
  if (mode === 'custom') {
    return customThreshold
  }
  return sensitivityModes.find((option) => option.value === mode)?.threshold ?? 90
}

function buildDecisionMap(preview: PreviewRow[]): Record<string, 'Keep A' | 'Keep B' | 'Keep Both' | 'Review'> {
  const decisions: Record<string, 'Keep A' | 'Keep B' | 'Keep Both' | 'Review'> = {}
  preview.forEach(row => {
    if (row.review_id) {
      decisions[String(row.review_id)] = (row.decision as any) || 'Review'
    }
  })
  return decisions
}

export default function LiteratureToolkit() {
  const [activeTab, setActiveTab] = useState<TabKey>('convert')
  const [convertFileInput, setConvertFileInput] = useState<File | null>(null)
  const [conversion, setConversion] = useState(conversionOptions[0].value)
  const [artifactLifetimeMinutes, setArtifactLifetimeMinutes] = useState(30)
  const [convertResult, setConvertResult] = useState<ConvertResponse | null>(null)
  const [dedupeFilesInput, setDedupeFilesInput] = useState<File[]>([])
  const [sensitivityMode, setSensitivityMode] = useState<SensitivityMode>('balanced')
  const [customFuzzyThreshold, setCustomFuzzyThreshold] = useState(90)
  const [dedupeResult, setDedupeResult] = useState<DeduplicateResponse | null>(null)
  const [reviewDecisions, setReviewDecisions] = useState<Record<string, 'Keep A' | 'Keep B' | 'Keep Both' | 'Review'>>({})

  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [converting, setConverting] = useState(false)
  const [deduplicating, setDeduplicating] = useState(false)
  const [applyingSettings, setApplyingSettings] = useState(false)
  const [savingReview, setSavingReview] = useState(false)
  const [finalizingReview, setFinalizingReview] = useState(false)

  const fuzzyThreshold = thresholdForMode(sensitivityMode, customFuzzyThreshold)

  const handleConvert = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!convertFileInput) {
      setError('Please select a file to convert.')
      return
    }
    setConverting(true)
    setError('')
    setStatus('Converting...')
    try {
      const result = await convertFile(convertFileInput, conversion, artifactLifetimeMinutes)
      setConvertResult(result)
      setStatus('Conversion complete.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Conversion failed')
      setStatus('')
    } finally {
      setConverting(false)
    }
  }

  const handleDeduplicate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (dedupeFilesInput.length === 0) {
      setError('Please select at least one file to deduplicate.')
      return
    }
    setDeduplicating(true)
    setError('')
    setStatus('Uploading, merging, and deduplicating...')
    try {
      const result = await deduplicateFiles(dedupeFilesInput, artifactLifetimeMinutes, fuzzyThreshold)
      setDedupeResult(result)
      setReviewDecisions(buildDecisionMap(result.review_preview ?? []))
      setStatus('Deduplication complete.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Deduplication failed')
      setStatus('')
    } finally {
      setDeduplicating(false)
    }
  }

  const handleApplyProcessingSettings = async () => {
    if (!dedupeResult?.job_id) return
    setApplyingSettings(true)
    setStatus('Recomputing fuzzy stage...')
    try {
      const result = await updateFuzzyThreshold(dedupeResult.job_id, fuzzyThreshold)
      setDedupeResult(result)
      setReviewDecisions(buildDecisionMap(result.review_preview ?? []))
      setStatus('Processing settings applied.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update fuzzy threshold')
      setStatus('')
    } finally {
      setApplyingSettings(false)
    }
  }

  const handleDecisionChange = (reviewId: string, value: 'Keep A' | 'Keep B' | 'Keep Both' | 'Review') => {
    setReviewDecisions((prev) => ({ ...prev, [reviewId]: value }))
  }

  const handleSaveReview = async () => {
    if (!dedupeResult?.job_id) return
    setSavingReview(true)
    setStatus('Saving review decisions...')
    try {
      await saveReviewDecisions(dedupeResult.job_id, reviewDecisions)
      setStatus('Review decisions saved.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save review decisions')
      setStatus('')
    } finally {
      setSavingReview(false)
    }
  }

  const handleFinalizeReview = async () => {
    if (!dedupeResult?.job_id) return
    setFinalizingReview(true)
    setStatus('Finalizing review and regenerating exports...')
    try {
      const result = await finalizeReview(dedupeResult.job_id, reviewDecisions)
      setDedupeResult(result)
      setReviewDecisions(buildDecisionMap(result.review_preview ?? []))
      setStatus('Review finalized and exports regenerated.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to finalize review')
      setStatus('')
    } finally {
      setFinalizingReview(false)
    }
  }

  const renderPreview = (rows: PreviewRow[]) => (
    <div className="overflow-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-slate-100 text-slate-700">
          <tr>
            {rows[0] ? Object.keys(rows[0]).map((key) => (
              <th key={key} className="whitespace-nowrap px-3 py-2 font-medium">{key}</th>
            )) : null}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-t border-slate-100">
              {Object.values(row).map((value, cellIndex) => (
                <td key={cellIndex} className="max-w-[280px] px-3 py-2 align-top text-slate-700">
                  {String(value ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )

  const renderRecordSummary = (sourceDatabase: string | null | undefined, title: string | null | undefined) => (
    <div className="space-y-1">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{sourceDatabase || 'Unknown source'}</div>
      <div className="max-w-[280px] text-slate-700">{String(title ?? '')}</div>
    </div>
  )

  return (
    <div className="flex flex-col">
      <main className="flex-1 mx-auto max-w-7xl px-6 py-8 w-full">
          <div className="animate-fade-in">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Literature Toolkit</h1>
                <p className="text-gray-600">Convert, merge, deduplicate, and export screening-ready study datasets.</p>
            </div>
            <div className="mb-6 flex gap-3">
              {(['convert', 'dedupe'] as TabKey[]).map((tab) => (
                <button
                  key={tab}
                  onClick={() => {
                    setActiveTab(tab)
                    setError('')
                    setStatus('')
                  }}
                  className={`rounded-full px-5 py-2 text-sm font-semibold transition-all ${
                    activeTab === tab
                      ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/20'
                      : 'bg-white text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  {tab === 'convert' ? 'Convert Format' : 'Merge & Deduplicate'}
                </button>
              ))}
            </div>

            {error ? <div className="mb-6 rounded-xl border-l-4 border-red-500 bg-red-50 p-4 text-red-800 shadow-sm">{error}</div> : null}
            {status ? <div className="mb-6 rounded-xl border-l-4 border-emerald-500 bg-emerald-50 p-4 text-emerald-800 shadow-sm">{status}</div> : null}

        {activeTab === 'convert' ? (
          <section className="animate-fade-in space-y-6">
            <form onSubmit={handleConvert} className="grid gap-6 md:grid-cols-2">
              <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-semibold text-slate-900">Upload Source File</h3>
                <div>
                  <input
                    type="file"
                    accept=".ris,.nbib,.csv"
                    required
                    onChange={(e) => setConvertFileInput(e.target.files?.[0] || null)}
                    className="block w-full text-sm text-slate-500 file:mr-4 file:rounded-full file:border-0 file:bg-emerald-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-emerald-700 hover:file:bg-emerald-100"
                  />
                  <p className="mt-2 text-xs text-slate-500">Supports .ris, .nbib, or .csv up to 50,000 records.</p>
                </div>
              </div>

              <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-semibold text-slate-900">Conversion Settings</h3>
                <div className="space-y-4">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-slate-700">Target Format</label>
                    <select
                      value={conversion}
                      onChange={(e) => setConversion(e.target.value)}
                      className="block w-full rounded-xl border-slate-300 bg-slate-50 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500"
                    >
                      {conversionOptions.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-slate-700">Artifact Expiration</label>
                    <select
                      value={artifactLifetimeMinutes}
                      onChange={(e) => setArtifactLifetimeMinutes(Number(e.target.value))}
                      className="block w-full rounded-xl border-slate-300 bg-slate-50 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500"
                    >
                      {artifactLifetimeOptions.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <div className="md:col-span-2">
                <button
                  type="submit"
                  disabled={converting}
                  className="w-full rounded-xl bg-slate-900 py-3.5 text-sm font-semibold text-white shadow-md hover:bg-slate-800 disabled:opacity-60"
                >
                  {converting ? 'Converting...' : 'Convert File'}
                </button>
              </div>
            </form>

            {convertResult && (
              <div className="animate-fade-in space-y-6">
                <div className="flex flex-col justify-between gap-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-6 sm:flex-row sm:items-center">
                  <div>
                    <h3 className="text-lg font-semibold text-emerald-900">Conversion Successful</h3>
                    <p className="text-sm text-emerald-700">
                      Processed <strong>{convertResult.records.toLocaleString()}</strong> records. Artifacts expire in{' '}
                      {artifactLifetimeOptions.find((o) => o.value === artifactLifetimeMinutes)?.label}.
                    </p>
                  </div>
                  <a
                    href={convertResult.download_url}
                    download={convertResult.download_name}
                    className="inline-flex items-center justify-center rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-emerald-500"
                  >
                    Download {convertResult.download_name}
                  </a>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <h3 className="mb-4 font-semibold text-slate-900">Converted Data Preview</h3>
                  {renderPreview(convertResult.preview)}
                </div>
              </div>
            )}
          </section>
        ) : (
          <section className="animate-fade-in space-y-8">
            <form onSubmit={handleDeduplicate} className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:col-span-1">
                <h3 className="font-semibold text-slate-900">Upload Datasets</h3>
                <div>
                  <input
                    type="file"
                    multiple
                    accept=".ris,.nbib,.csv"
                    required
                    onChange={(e) => setDedupeFilesInput(Array.from(e.target.files || []))}
                    className="block w-full text-sm text-slate-500 file:mr-4 file:rounded-full file:border-0 file:bg-emerald-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-emerald-700 hover:file:bg-emerald-100"
                  />
                  <p className="mt-2 text-xs text-slate-500">
                    Select multiple files to merge and deduplicate. Supports .ris, .nbib, or .csv up to 50,000 combined records.
                  </p>
                </div>
                {dedupeFilesInput.length > 0 && (
                  <ul className="mt-3 max-h-32 overflow-y-auto rounded-lg bg-slate-50 p-2 text-xs text-slate-600">
                    {dedupeFilesInput.map((f, i) => (
                      <li key={i} className="truncate px-2 py-1">
                        • {f.name}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
                <h3 className="font-semibold text-slate-900">Processing Settings</h3>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-slate-700">Fuzzy Matching Sensitivity</label>
                    <select
                      value={sensitivityMode}
                      onChange={(e) => setSensitivityMode(e.target.value as SensitivityMode)}
                      className="block w-full rounded-xl border-slate-300 bg-slate-50 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500"
                    >
                      {sensitivityModes.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                    {sensitivityMode === 'custom' && (
                      <div className="mt-3">
                        <div className="flex justify-between text-xs text-slate-500">
                          <span>Loose (85%)</span>
                          <span>Strict (99%)</span>
                        </div>
                        <input
                          type="range"
                          min="85"
                          max="99"
                          value={customFuzzyThreshold}
                          onChange={(e) => setCustomFuzzyThreshold(Number(e.target.value))}
                          className="mt-1 w-full accent-emerald-600"
                        />
                        <div className="mt-1 text-center text-xs font-medium text-slate-700">Current: {customFuzzyThreshold}% Match Required</div>
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-slate-700">Artifact Expiration</label>
                    <select
                      value={artifactLifetimeMinutes}
                      onChange={(e) => setArtifactLifetimeMinutes(Number(e.target.value))}
                      className="block w-full rounded-xl border-slate-300 bg-slate-50 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500"
                    >
                      {artifactLifetimeOptions.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={handleApplyProcessingSettings}
                      disabled={!dedupeResult || applyingSettings}
                      className="mt-4 w-full rounded-xl border border-slate-200 bg-white py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                    >
                      {applyingSettings ? 'Recomputing...' : 'Recompute With New Settings'}
                    </button>
                    <p className="mt-2 text-[10px] text-slate-500 leading-tight">
                      Adjusting settings will immediately recompute the fuzzy duplicate stage based on the currently uploaded datasets without needing a full re-upload.
                    </p>
                  </div>
                </div>
              </div>

              <div className="md:col-span-2 lg:col-span-3">
                <button
                  type="submit"
                  disabled={deduplicating}
                  className="w-full rounded-xl bg-slate-900 py-3.5 text-sm font-semibold text-white shadow-md hover:bg-slate-800 disabled:opacity-60"
                >
                  {deduplicating ? 'Processing Pipeline...' : 'Run Merge & Deduplication'}
                </button>
              </div>
            </form>

            {dedupeResult && (
              <div className="animate-fade-in space-y-6">
                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold">Export Artifacts</h3>
                    {dedupeResult.finalized ? (
                       <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                         <span className="h-1.5 w-1.5 rounded-full bg-emerald-600"></span>
                         Finalized
                       </span>
                    ) : (
                       <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
                         <span className="h-1.5 w-1.5 rounded-full bg-amber-600"></span>
                         Pending Review
                       </span>
                    )}
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    {Object.values(dedupeResult.artifacts).map((artifact) => (
                      <a
                        key={artifact.artifact_id}
                        href={artifact.download_url}
                        download={artifact.filename}
                        className="group flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-4 transition-all hover:border-emerald-300 hover:bg-emerald-50 hover:shadow-sm"
                      >
                        <div className="truncate pr-4 text-sm font-medium text-slate-700 group-hover:text-emerald-800">{artifact.filename}</div>
                        <svg
                          className="h-5 w-5 text-slate-400 group-hover:text-emerald-600"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                      </a>
                    ))}
                  </div>
                  {!dedupeResult.finalized && (
                     <p className="mt-4 text-sm text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100">
                       Please complete the duplicate review below. Once finalized, the screening exports will be regenerated to reflect your decisions.
                     </p>
                  )}
                </div>

            <div className="space-y-4">
              {dedupeResult.review_preview.length > 0 ? (
                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="mb-4 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                    <div>
                      <h3 className="font-semibold text-slate-900">Fuzzy Duplicate Review</h3>
                      <p className="mt-1 text-sm text-slate-600">
                        The automated pipeline flagged {dedupeResult.review_preview.length} pairs as potential fuzzy duplicates (confidence {'<'} 100%).
                      </p>
                    </div>
                  </div>

                  <div className="overflow-auto rounded-xl border border-slate-200 shadow-sm">
                    <table className="min-w-full text-left text-sm">
                      <thead className="bg-slate-100 text-slate-700">
                        <tr>
                          <th className="px-4 py-3 font-medium">Score</th>
                          <th className="px-4 py-3 font-medium w-2/5">Record A</th>
                          <th className="px-4 py-3 font-medium w-2/5">Record B</th>
                          <th className="px-4 py-3 font-medium bg-slate-200 w-48">Decision</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {dedupeResult.review_preview.map((row) => (
                          <tr key={String(row.review_id)} className="transition-colors hover:bg-slate-50">
                            <td className="px-4 py-3 text-center align-middle">
                              <span
                                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                                  Number(row.similarity_score) >= 95
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : Number(row.similarity_score) >= 90
                                    ? 'bg-blue-100 text-blue-800'
                                    : 'bg-amber-100 text-amber-800'
                                }`}
                              >
                                {row.similarity_score}%
                              </span>
                            </td>
                            <td className="px-4 py-3 align-top">
                              {renderRecordSummary(row.source_a as string, row.title_a as string)}
                            </td>
                            <td className="px-4 py-3 align-top">
                              {renderRecordSummary(row.source_b as string, row.title_b as string)}
                            </td>
                            <td className="bg-slate-50 px-4 py-3 align-top">
                              <select
                                value={reviewDecisions[String(row.review_id)] || 'Review'}
                                onChange={(e) => handleDecisionChange(String(row.review_id), e.target.value as any)}
                                className={`block w-full rounded-lg border-slate-300 py-2 pl-3 pr-8 text-sm focus:border-emerald-500 focus:outline-none focus:ring-emerald-500 ${
                                  reviewDecisions[String(row.review_id)] === 'Review' ? 'bg-amber-50 font-medium text-amber-900 border-amber-200' : 'bg-white text-slate-700'
                                }`}
                              >
                                <option value="Review" disabled className="text-slate-400">Needs Review</option>
                                <option>Keep A</option>
                                <option>Keep B</option>
                                <option>Keep Both</option>
                                <option>Review</option>
                              </select>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="mt-6 flex flex-wrap justify-end gap-3">
                    <button
                      onClick={handleSaveReview}
                      disabled={savingReview}
                      className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 disabled:opacity-60 hover:bg-slate-50"
                    >
                      {savingReview ? 'Saving...' : 'Save Progress'}
                    </button>
                    <button
                      onClick={handleFinalizeReview}
                      disabled={finalizingReview}
                      className="rounded-xl bg-emerald-600 px-4 py-3 text-sm font-medium text-white hover:bg-emerald-500 shadow-sm disabled:opacity-60"
                    >
                      {finalizingReview ? 'Finalizing...' : 'Finalize & Export'}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-slate-900">Duplicate Review Complete</h3>
                    <p className="mt-1 text-sm text-slate-600">No fuzzy duplicates require manual review at this threshold level.</p>
                  </div>
                  <button
                    onClick={handleFinalizeReview}
                    disabled={finalizingReview || dedupeResult.finalized}
                    className="rounded-xl bg-emerald-600 px-4 py-3 text-sm font-medium text-white hover:bg-emerald-500 shadow-sm disabled:opacity-60"
                  >
                    {finalizingReview ? 'Finalizing...' : dedupeResult.finalized ? 'Finalized' : 'Generate Screening Exports'}
                  </button>
                </div>
              )}

              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-semibold">Analytics Dashboard</h3>
                <div className="mt-4 grid gap-3 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                  {[
                    ['Total Imported', dedupeResult.report.records_imported],
                    ['Exact Matches Removed', dedupeResult.report.removed_by_exact_title],
                    ['Fuzzy Matches Removed', dedupeResult.report.removed_by_fuzzy],
                    ['Final Retained', dedupeResult.report.final_records]
                  ].map(([label, value]) => (
                    <div key={label as string} className="rounded-xl bg-slate-50 px-4 py-3 border border-slate-100">
                      <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</div>
                      <div className="mt-1 text-2xl font-semibold text-slate-800">{String(value ?? '-')}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-semibold">Preview</h3>
                <p className="mt-1 text-sm text-slate-600">Deduplicated master spreadsheet preview.</p>
                <div className="mt-4">{renderPreview(dedupeResult.preview)}</div>
              </div>
            </div>
          </section>
        )}
          </div>
      </main>
    </div>
  )
}
