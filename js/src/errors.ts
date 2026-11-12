import { CLOSE_CODE_BASE, ERRORS, type ErrorCode } from './generated/spec.ts'

const NORMAL_CLOSES = new Set([1000, 1001])

/** The fields a {@link TaviaError} is built from; all optional. */
export interface TaviaErrorInit {
  /** The API's error code, such as `unauthorized`. */
  code?: string | null
  /** A readable message; defaults to the code's standard message. */
  message?: string
  /** The HTTP status. */
  http?: number | null
  /** The WebSocket close code, for a socket failure. */
  closeCode?: number | null
  /** The text-to-speech context the error belongs to. */
  contextId?: string | null
  /** The failing request field, when the server names one. */
  param?: string | null
}

/** Every failure the SDK reports: the API's error code (when the server named one) and its HTTP status. */
export class TaviaError extends Error {
  /** The API's error code, or null when the server did not name one. */
  readonly code: string | null
  /** The HTTP status, or null when there is none. */
  readonly http: number | null
  /** The WebSocket close code, for a socket failure. */
  readonly closeCode: number | null
  /** The text-to-speech context the error belongs to, or null for the whole stream. */
  readonly contextId: string | null
  /** The failing request field, as `session.tools[1].name`, when the server names one. */
  readonly param: string | null

  constructor(init: TaviaErrorInit = {}) {
    const known = init.code && Object.hasOwn(ERRORS, init.code) ? ERRORS[init.code as ErrorCode] : undefined
    super(init.message ?? known?.message ?? init.code ?? 'request failed')
    this.name = new.target.name
    this.code = init.code ?? null
    this.http = init.http ?? known?.http ?? null
    this.closeCode = init.closeCode ?? null
    this.contextId = init.contextId ?? null
    this.param = init.param ?? null
  }
}

/** HTTP 400: the request is malformed or has an invalid field. */
export class InvalidRequestError extends TaviaError {}
/** HTTP 401: the API key or token is missing, invalid or expired. */
export class AuthenticationError extends TaviaError {}
/** HTTP 402: the account has no credit left. */
export class InsufficientCreditError extends TaviaError {}
/** HTTP 403: the key or token may not do this. */
export class PermissionDeniedError extends TaviaError {}
/** HTTP 404: the resource does not exist. */
export class NotFoundError extends TaviaError {}
/** HTTP 408: the request took too long. */
export class RequestTimeoutError extends TaviaError {}
/** HTTP 409 or 410: the request conflicts with the resource's state, or the resource is gone. */
export class ConflictError extends TaviaError {}
/** HTTP 413: the request or file is too large. */
export class TooLargeError extends TaviaError {}
/** HTTP 415: the media type is not supported. */
export class UnsupportedMediaError extends TaviaError {}
/** HTTP 422: the request is well formed but cannot be processed. */
export class UnprocessableError extends TaviaError {}
/** HTTP 429: too many requests or sessions; retry later. */
export class RateLimitError extends TaviaError {}
/** HTTP 5xx: the server failed. */
export class ServerError extends TaviaError {}

/**
 * The server could not be reached, or a socket closed before it opened. For a socket, `closeCode` carries the
 * server's reason (4000 + HTTP status); for a network failure it is null and `cause` holds the underlying error.
 */
export class ConnectError extends TaviaError {
  constructor(closeCode: number | null, options: { cause?: unknown } = {}) {
    super(closeCode === null
      ? { message: 'could not reach the server' }
      : { ...closeInit(closeCode), message: `the session closed before it opened (${closeCode})`, closeCode })
    if (options.cause !== undefined) Object.defineProperty(this, 'cause', { value: options.cause })
  }
}

/** Thrown by any send on a session whose socket is closed or closing; `closeCode` is the close, once known. */
export class SessionClosedError extends TaviaError {
  constructor(closeCode: number | null = null) {
    super({ message: closeCode === null ? 'the session is closed' : `the session is closed (${closeCode})`, closeCode })
  }
}

type ErrorClass = new (init?: TaviaErrorInit) => TaviaError

/** The error class for each HTTP status; other 5xx statuses map to {@link ServerError}. */
export const STATUS_CLASSES: Readonly<Record<number, ErrorClass>> = {
  400: InvalidRequestError,
  401: AuthenticationError,
  402: InsufficientCreditError,
  403: PermissionDeniedError,
  404: NotFoundError,
  408: RequestTimeoutError,
  409: ConflictError,
  410: ConflictError,
  413: TooLargeError,
  415: UnsupportedMediaError,
  422: UnprocessableError,
  429: RateLimitError,
}

function classFor(http: number | null | undefined): ErrorClass {
  if (http && STATUS_CLASSES[http]) return STATUS_CLASSES[http]
  return http && http >= 500 ? ServerError : TaviaError
}

/** Every API error code and the error class it raises. */
export const ERROR_CLASSES = Object.fromEntries(
  (Object.keys(ERRORS) as ErrorCode[]).map((code) => [code, classFor(ERRORS[code].http)]),
) as Readonly<Record<ErrorCode, ErrorClass>>

/** The typed error for an API error code; `extra.http` is used only for a code the SDK does not know. */
export function errorForCode(code: string, message?: string, extra: TaviaErrorInit = {}): TaviaError {
  const http = Object.hasOwn(ERRORS, code) ? ERRORS[code as ErrorCode].http : extra.http
  return new (classFor(http))({ ...extra, code, message, http })
}

function closeInit(closeCode: number): TaviaErrorInit {
  const http = closeCode - CLOSE_CODE_BASE
  const codes = (Object.keys(ERRORS) as ErrorCode[]).filter((c) => ERRORS[c].http === http)
  return { http: http >= 400 && http < 600 ? http : null, code: codes.length === 1 ? codes[0] : null }
}

/** The error a WebSocket close code reports, or null for a normal close (1000 or 1001). */
export function errorForClose(closeCode: number): TaviaError | null {
  if (NORMAL_CLOSES.has(closeCode)) return null
  const init = closeInit(closeCode)
  return new (classFor(init.http))({ ...init, closeCode, message: `the session closed (${closeCode})` })
}

/** The typed error for an HTTP error response; the body is `{"error": {code, message}}` or `{"error": "code"}`. */
export function errorForHttp(status: number, body: unknown): TaviaError {
  const err = (body as { error?: unknown } | null)?.error
  const code = typeof err === 'string' ? err : (err as { code?: string } | undefined)?.code
  const fields = typeof err === 'object' && err ? (err as { message?: string, param?: string }) : {}
  return new (classFor(status))({ code: code ?? null, message: fields.message, http: status, param: fields.param ?? null })
}

/** The message the agent gets when a tool handler fails without a {@link ToolError}. */
export const TOOL_FAILED = 'tool_failed'

/** Throw from a tool handler to tell the agent why: this message, and only this, reaches the model. */
export class ToolError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ToolError'
  }
}
