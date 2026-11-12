import { errorForCode } from '../errors.ts'
import { SURFACE } from '../generated/spec.ts'
import { request, type HttpOptions } from '../transport/http.ts'
import { DEFAULT_URLS } from '../transport/urls.ts'

/** The file transcription endpoint on the public API. */
export const STT_FILES_URL = DEFAULT_URLS.sttFiles
const POLL_MS = 2000

/** A transcription job's status: `queued`, `running`, `done` or `failed`. */
export type SttJobStatus = (typeof SURFACE.stt.jobStatuses)[number]

/** One word and its times, in ms from the start of the file. */
export interface SttWord { text: string, start_ms: number, end_ms: number }

/** One stretch of speech in a file transcript; times are in ms from the start of the file. */
export interface SttSegment {
  /** Where the segment starts. */
  start_ms: number
  /** Where the segment ends. */
  end_ms: number
  /** The segment's text. */
  text: string
  /** The language heard, such as `en`. */
  language: string
  /** 0..1, or null when not available. */
  confidence: number | null
  /** The segment's words with their times. */
  words: SttWord[]
  /** Hesitations in this segment, in ms from the start of the file; absent when none. `before` counts its words. */
  fillers?: Array<{ type: 'uh' | 'um', start_ms: number, end_ms: number, before: number }>
}

/** A file's transcript: the full text, the audio length in seconds, the decoder used and the segments. */
export interface SttFileResult { text: string, duration_s: number, decoder: string, segments: SttSegment[] }

/** A transcription job: its status, progress (0..1 or null), and the result or error code once it ends. */
export interface SttJob { status: SttJobStatus, progress: number | null, result?: SttFileResult, error?: string }

/** An audio file to transcribe, as a Blob or raw bytes. */
export type AudioFile = Blob | ArrayBuffer | Uint8Array

/** Options for `tavia.stt.transcribe`. */
export interface TranscribeOptions {
  /** Hint words, such as names and product terms, the recognizer should expect. */
  terms?: string[]
  /** How often to check the job, in ms (default 2000). */
  pollMs?: number
  /** Keep the job on the server after reading it (it expires an hour after it finishes). */
  keep?: boolean
}

/** Options for the file transcription functions; most apps use `tavia.stt` instead. */
export interface SttFilesOptions extends HttpOptions {
  /** The file transcription endpoint; defaults to the public API. */
  url?: string
  /** Waits between polls; replace it to control time in tests. */
  sleep?: (ms: number) => Promise<void>
}

const wait = (ms: number): Promise<void> => new Promise((r) => setTimeout(r, ms))
const jobUrl = (opts: SttFilesOptions, id: string): string => `${opts.url ?? STT_FILES_URL}/${encodeURIComponent(id)}`

function asBlob(file: AudioFile): Blob {
  return file instanceof Blob ? file : new Blob([file instanceof Uint8Array ? file.slice() : file])
}

/** Uploads a file for transcription and returns the job id. */
export async function createJob(opts: SttFilesOptions, file: AudioFile, terms?: string[]): Promise<string> {
  const form = new FormData()
  form.append('file', asBlob(file), 'audio')
  if (terms?.length) form.append('terms', terms.join('\n'))
  const res = await request<{ job_id: string }>(opts, opts.url ?? STT_FILES_URL, { method: 'POST', body: form })
  return res.job_id
}

/** A job's status, and its transcript once done. */
export function getJob(opts: SttFilesOptions, jobId: string): Promise<SttJob> {
  return request<SttJob>(opts, jobUrl(opts, jobId))
}

/** Deletes a job and its transcript from the server. */
export async function deleteJob(opts: SttFilesOptions, jobId: string): Promise<void> {
  await request<null>(opts, jobUrl(opts, jobId), { method: 'DELETE' })
}

/** Uploads, polls until done, deletes the job (unless `keep`) and returns the transcript; a failed job throws its typed error. */
export async function transcribe(opts: SttFilesOptions, file: AudioFile, t: TranscribeOptions = {}): Promise<SttFileResult> {
  const id = await createJob(opts, file, t.terms)
  try {
    for (;;) {
      const job = await getJob(opts, id)
      if (job.status === 'done' && job.result) return job.result
      if (job.status === 'failed') throw errorForCode(job.error ?? 'transcription_failed')
      await (opts.sleep ?? wait)(t.pollMs ?? POLL_MS)
    }
  } finally {
    if (!t.keep) await deleteJob(opts, id).catch(() => undefined)
  }
}
