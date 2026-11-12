# Changelog

Both packages, `@tavia/sdk` (npm) and `tavia` (PyPI), share one version. This project follows
[Semantic Versioning](https://semver.org); until 1.0.0, a minor release may change the API, and every change is
listed here.

## 0.9.0

The first public release.

### Added

- Realtime voice sessions: `tavia.realtime.connect()`, typed session options, friendly events (`transcript`, `turn`,
  `tool_call`, `timing`, `ended` and more), every wire event typed, tool handlers, `interrupt()` with playback cut
  at the point the caller heard.
- Speech-to-text: live streams with formatted finals, and file transcription (now or as a job).
- Text-to-speech: live streams, one-off renders to WAV, and the voice list.
- Browser tokens: `tokens.create()` mints a short-lived token on your server for a page on an allowed origin.
- Tool helpers: `functionTool` / `function_tool` with a required read or write effect, `templateTool` /
  `template_tool`, and `checkTools` / `check_tools`, which report what a session would refuse.
- Browser audio (TypeScript): microphone capture, playback, a microphone quality meter and a pre-call check.
- Typed errors: `TaviaError` and a subclass per kind (`AuthenticationError`, `RateLimitError`,
  `InvalidRequestError`, `ServerError`, `ConnectError`, `SessionClosedError` and more).
- HTTP requests retry rate limits and unavailable answers with backoff, honouring `Retry-After`; `maxRetries` /
  `max_retries` sets how often.
- Examples for both languages: a browser voice page with its token server, transcribing a file, text-to-speech.

### Changed (from pre-release builds)

- Realtime sessions use the standard event names and session shape: `response.output_audio.delta`,
  `response.output_audio_transcript.delta` / `.done`, `conversation.item.added` / `.done`, with Tavia's own session
  options sent under `tavia`. Session options you pass are unchanged.
- Every endpoint defaults to `https://api.tavialabs.com/v1`; the live speech-to-text socket keeps its own host.
- An API key is refused in a browser (TypeScript): pages use a token.

### Deprecated

- The old event names (`response.audio.delta`, `response.audio.done`, `response.audio_transcript.delta`,
  `response.audio_transcript.done`) still subscribe to their renamed events, with a warning.
- `dialect: 'beta'` keeps the older wire format for integrations written against it.
