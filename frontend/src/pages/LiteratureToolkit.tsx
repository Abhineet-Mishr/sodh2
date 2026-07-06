import { useAuth } from "../context/AuthContext";
import { useMemo, useState } from 'react'
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

export default function LiteratureToolkit() {

  const [activeMainTab, setActiveMainTab] = useState<MainTabKey>('literature-toolkit')
  const [activeTab, setActiveTab] = useState<TabKey>('convert')
  const [convertFileInput, setConvertFileInput] = useState<File | null>(null)
  const [conversion, setConversion] = useState(conversionOptions[0].value)
  const [artifactLifetimeMinutes, setArtifactLifetimeMinutes] = useState(30)
  const [convertResult, setConvertResult] = useState<ConvertResponse | null>(null)
  const [dedupeFilesInput, setDedupeFilesInput] = useState<File[]>([])
  const [dedupeResult, setDedupeResult] = useState<DeduplicateResponse | null>(null)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [reviewDecisions, setReviewDecisions] = useState<Record<string, string>>({})
  const [savingReview, setSavingReview] = useState(false)
  const [finalizingReview, setFinalizingReview] = useState(false)
  const [applyingSettings, setApplyingSettings] = useState(false)
  const [sensitivityMode, setSensitivityMode] = useState<SensitivityMode>('aggressive')
  const [customThreshold, setCustomThreshold] = useState(90)

  const fuzzyThreshold = useMemo(() => thresholdForMode(sensitivityMode, customThreshold), [sensitivityMode, customThreshold])

  const analytics = useMemo(() => {
    const report: ProcessingReport = dedupeResult?.report ?? {}
    return [
      ['Records Imported', report.records_imported],
      ['After DOI Deduplication', report.records_after_doi],
      ['After PMID Deduplication', report.records_after_pmid],
      ['After Exact Title Deduplication', report.records_after_exact_title],
      ['After Fuzzy Deduplication', report.records_after_fuzzy],
      ['Final Records', report.final_records],
    ] as const
  }, [dedupeResult])

  async function handleConvert() {
    if (!convertFileInput) {
      setError('Please upload a file first.')
      return
    }
    setError('')
    setStatus('Uploading and converting...')
    try {
      const result = await convertFile(convertFileInput, conversion, artifactLifetimeMinutes)
      setConvertResult(result)
      setStatus('Conversion complete.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Conversion failed')
      setStatus('')
    }
  }

  async function handleDeduplicate() {
    if (!dedupeFilesInput.length) {
      setError('Please upload at least one RIS or NBIB file.')
      return
    }
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
    }
  }

  async function handleApplyProcessingSettings() {
    if (!dedupeResult) {
      return
    }
    setError('')
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

  async function handleSaveReview() {
    if (!dedupeResult) return
    setError('')
    setSavingReview(true)
    setStatus('Saving review decisions...')
    try {
      const result = await saveReviewDecisions(dedupeResult.job_id, reviewDecisions)
      setDedupeResult((current) => (current ? { ...current, review_preview: result.review_preview as PreviewRow[] } : current))
      setStatus('Review decisions saved.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save review decisions')
      setStatus('')
    } finally {
      setSavingReview(false)
    }
  }

  async function handleFinalizeReview() {
    if (!dedupeResult) return
    setError('')
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
  </>
  )

  const renderRecordSummary = (sourceDatabase: string | null | undefined, title: string | null | undefined) => (
    <div className="space-y-1">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{sourceDatabase || 'Unknown source'}</div>
      <div className="max-w-[280px] text-slate-700">{String(title ?? '')}</div>
    </div>
  </>
  )
  return (
<>
        {/* Mobile Navigation */}
        <div className="md:hidden border-t border-slate-200 flex p-2 overflow-x-auto gap-2">
           {(['literature-toolkit', 'research-suggestions'] as MainTabKey[]).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveMainTab(tab)}
                  className={`flex-shrink-0 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeMainTab === tab
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  {tab === 'literature-toolkit' ? 'Literature Toolkit' : 'Research Suggestions'}
                </button>
            ))}
        </div>
      </header>

      <main className="flex-1 mx-auto max-w-7xl px-6 py-8 w-full">
        {activeMainTab === 'research-suggestions' ? (
          <ResearchSuggestionsPage />
        ) : (
          <div className="animate-fade-in">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Literature Toolkit</h1>
                <p className="text-gray-600">Convert, merge, deduplicate, and export screening-ready study datasets.</p>
            </div>
            <div className="mb-6 flex gap-3">
              {(['convert', 'dedupe'] as TabKey[]).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`rounded-full px-5 py-2.5 text-sm font-medium transition-all ${
                    activeTab === tab
                      ? 'bg-slate-900 text-white shadow-md'
                      : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {tab === 'convert' ? 'Convert Files' : 'Deduplicate Studies'}
                </button>
              ))}
            </div>

        {error ? <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-rose-700">{error}</div> : null}
        {status ? <div className="mb-4 rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sky-800">{status}</div> : null}

        {activeTab === 'convert' ? (
          <section className="grid gap-6 lg:grid-cols-[380px,1fr]">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold">Convert Files</h2>
              <p className="mt-1 text-sm text-slate-600">Upload one RIS, NBIB, or CSV file and convert it into a standard format.</p>

              <label className="mt-5 block text-sm font-medium text-slate-700">Artifact Lifetime</label>
              <select
                value={artifactLifetimeMinutes}
                onChange={(event) => setArtifactLifetimeMinutes(Number(event.target.value))}
                className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              >
                {artifactLifetimeOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>

              <label className="mt-5 block text-sm font-medium text-slate-700">File</label>
              <input
                type="file"
                accept=".ris,.nbib,.csv"
                onChange={(event) => setConvertFileInput(event.target.files?.[0] ?? null)}
                className="mt-2 block w-full text-sm"
              />

              <label className="mt-5 block text-sm font-medium text-slate-700">Conversion</label>
              <select
                value={conversion}
                onChange={(event) => setConversion(event.target.value)}
                className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              >
                {conversionOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>

              <button
                onClick={handleConvert}
                className="mt-6 w-full rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white hover:bg-slate-800"
              >
                Parse → Normalize → Download
              </button>

              {convertResult ? (
                <a
                  href={convertResult.download_url}
                  className="mt-3 block rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-center text-sm font-medium text-slate-900"
                >
                  Download converted file
                </a>
              ) : null}
            </div>

            <div className="space-y-4">
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-semibold">Progress</h3>
                <div className="mt-3 grid gap-3 md:grid-cols-4">
                  {['Upload', 'Parse', 'Normalize', 'Preview'].map((step) => (
                    <div key={step} className="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-700">{step}</div>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-semibold">Preview</h3>
                <p className="mt-1 text-sm text-slate-600">First 20 rows from the standardized output.</p>
                <div className="mt-4">{convertResult ? renderPreview(convertResult.preview) : <div className="text-sm text-slate-500">No preview yet.</div>}</div>
              </div>
            </div>
          </section>
        ) : (
          <section className="grid gap-6 lg:grid-cols-[380px,1fr]">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold">Deduplicate Studies</h2>
              <p className="mt-1 text-sm text-slate-600">Upload multiple RIS or NBIB files to merge and deduplicate them for screening.</p>

              <details className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4" open>
                <summary className="cursor-pointer text-sm font-semibold text-slate-900">Processing Settings</summary>
                <div className="mt-4 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700">Artifact Lifetime</label>
                    <select
                      value={artifactLifetimeMinutes}
                      onChange={(event) => setArtifactLifetimeMinutes(Number(event.target.value))}
                      className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
                    >
                      {artifactLifetimeOptions.map((option) => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700">Duplicate Sensitivity</label>
                    <select
                      value={sensitivityMode}
                      onChange={(event) => setSensitivityMode(event.target.value as SensitivityMode)}
                      className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
                    >
                      {sensitivityModes.map((option) => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                      ))}
                    </select>
                  </div>

                  {sensitivityMode === 'custom' ? (
                    <div>
                      <div className="flex items-center justify-between text-sm text-slate-700">
                        <span>Custom threshold</span>
                        <span className="font-semibold">{customThreshold}%</span>
                      </div>
                      <input
                        type="range"
                        min={85}
                        max={99}
                        value={customThreshold}
                        onChange={(event) => setCustomThreshold(Number(event.target.value))}
                        className="mt-2 w-full"
                      />
                    </div>
                  ) : (
                    <div className="text-sm text-slate-600">Selected threshold: {fuzzyThreshold}%</div>
                  )}

                  <button
                    onClick={handleApplyProcessingSettings}
                    disabled={!dedupeResult || applyingSettings}
                    className="w-full rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
                  >
                    {applyingSettings ? 'Applying...' : 'Apply Settings to Current Job'}
                  </button>
                </div>
              </details>

              <label className="mt-5 block text-sm font-medium text-slate-700">Files</label>
              <input
                type="file"
                accept=".ris,.nbib"
                multiple
                onChange={(event) => setDedupeFilesInput(Array.from(event.target.files ?? []))}
                className="mt-2 block w-full text-sm"
              />

              <button
                onClick={handleDeduplicate}
                className="mt-6 w-full rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white hover:bg-slate-800"
              >
                Merge → Deduplicate → Export
              </button>

              {dedupeResult ? (
                <div className="mt-3 space-y-2">
                  {Object.entries(dedupeResult.artifacts).map(([key, value]) => (
                    <a
                      key={key}
                      href={value.download_url}
                      className="block rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-900"
                    >
                      Download {key.replaceAll('_', ' ')} ({value.filename})
                    </a>
                  ))}
                </div>
              ) : null}

              {dedupeResult ? (
                <div className="mt-4 grid gap-2">
                  <button
                    onClick={handleSaveReview}
                    disabled={savingReview}
                    className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 disabled:opacity-60"
                  >
                    {savingReview ? 'Saving...' : 'Save Review Decisions'}
                  </button>
                  <button
                    onClick={handleFinalizeReview}
                    disabled={finalizingReview}
                    className="rounded-xl bg-emerald-600 px-4 py-3 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-60"
                  >
                    {finalizingReview ? 'Finalizing...' : 'Finalize Review'}
                  </button>
                </div>
              ) : null}
            </div>

            <div className="space-y-4">
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-semibold">Analytics Dashboard</h3>
                <div className="mt-4 grid gap-3 md:grid-cols-3">
                  {analytics.map(([label, value]) => (
                    <div key={label} className="rounded-xl bg-slate-50 px-4 py-3">
                      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
                      <div className="mt-2 text-2xl font-semibold">{String(value ?? '-')}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-semibold">Duplicate Review</h3>
                <p className="mt-1 text-sm text-slate-600">Review likely duplicates before exporting the final spreadsheet.</p>
                <div className="mt-4 overflow-auto rounded-xl border border-slate-200">
                  <table className="min-w-full text-left text-sm">
                    <thead className="bg-slate-100">
                      <tr>
                        <th className="px-3 py-2">Record A</th>
                        <th className="px-3 py-2">Record B</th>
                        <th className="px-3 py-2">Score</th>
                        <th className="px-3 py-2">Decision</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(dedupeResult?.review_preview ?? []).map((row, index) => (
                        <tr key={String(row.review_id ?? index)} className="border-t border-slate-100">
                          <td className="max-w-[260px] px-3 py-2">
                            {renderRecordSummary(String(row.record_a_source_database ?? ''), String(row.record_a_title ?? ''))}
                          </td>
                          <td className="max-w-[260px] px-3 py-2">
                            {renderRecordSummary(String(row.record_b_source_database ?? ''), String(row.record_b_title ?? ''))}
                          </td>
                          <td className="px-3 py-2">{String(row.similarity_score ?? '')}</td>
                          <td className="px-3 py-2">
                            <select
                              value={reviewDecisions[String(row.review_id ?? index)] ?? String(row.decision ?? 'Review')}
                              onChange={(event) =>
                                setReviewDecisions((current) => ({
                                  ...current,
                                  [String(row.review_id ?? index)]: event.target.value,
                                }))
                              }
                              className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-sm"
                            >
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
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-semibold">Preview</h3>
                <p className="mt-1 text-sm text-slate-600">Deduplicated master spreadsheet preview.</p>
                <div className="mt-4">{dedupeResult ? renderPreview(dedupeResult.preview) : <div className="text-sm text-slate-500">No results yet.</div>}</div>
              </div>
            </div>
          </section>
        )}
          </div>
        )}
      </main>
  </>
  )
}
