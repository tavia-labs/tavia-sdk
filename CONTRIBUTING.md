# Contributing

Thanks for helping. Bug reports and small, focused pull requests are welcome.

## Setup and checks

TypeScript (`js/`, Node 22 or later):

```sh
cd js
npm ci
npm run lint && npm run typecheck && npm test && npm run build
```

Python (`python/`, 3.11 or later):

```sh
cd python
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
ruff check . && ruff format --check . && pytest
```

## Pull requests

- One change per pull request, with a test that fails without it.
- Keep both SDKs in step: a change to one language's public API needs the same change in the other.
- Run every check above before you open the pull request; CI runs the same ones.

## Generated files

Files under `generated/` (event types, error codes, limits) are produced from the API specification, which is
maintained upstream. Do not edit them by hand: open an issue describing the change instead, and we will update the
specification and regenerate them.

## Security issues

Please do not open public issues for security problems; see [SECURITY.md](SECURITY.md).
