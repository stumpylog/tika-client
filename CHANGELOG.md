# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-08-27

### Breaking Change

- **Requires Tika Server 4.0+.** Tika 4 is a wire-breaking release; use `tika-client` 1.0.0 for
  Tika 3.x.
- **Requires Python 3.11+.** 3.10 reaches end of life in October 2026, and this release uses
  `ExceptionGroup`.
- **A failed parse now raises instead of returning empty content.** Tika 4 reports parse
  failures as a `200`, where 3.x returned a `500`. `tika.*` and `metadata.*` raise
  `TikaContainerParseError` when the document failed outright, and `TikaEmbeddedParseError`
  when only an embedded member did. **The second fires on documents that previously appeared
  to succeed**: an archive or email with one unreadable attachment came back with the good
  content and the failed member's text silently absent. The exception carries `partial`, the
  response as parsed, so nothing is lost. There is no option to disable raising; catch the
  exception where you want best-effort extraction. `rmeta.*` does not raise, so entries that
  parsed are not discarded. See "Parse Failures" in the README.
- Tika-computed metadata keys moved from `X-TIKA:` to `tk:` (`X-TIKA:content` -> `tk:content`).
  `TikaKey.Parsers`, `TikaKey.Parser_Full`, `TikaKey.Parse_Time` and `TikaKey.Content` hold the
  new spellings. `dc:*`, `xmp:*` and `cp:*` are unchanged, being the file's own assertions
  rather than Tika's. `meta:*` is mostly unchanged, but Office custom properties move to
  `office:*` and curated MAPI keys move to `mapi:*` (`meta:mapi-importance` -> `mapi:importance`).
- **If you index `result.data` by string, check your keys.** Tika 4 renamed roughly 50 more keys
  than the four above, kebab-casing format namespaces (`pdf:hasMarkedContent` ->
  `pdf:has-marked-content`) and moving others between prefixes (`resourceName` ->
  `tk:resource-name`). See [Metadata changes in Tika 4](https://tika.apache.org/docs/4.0.x/migration-to-4x/metadata-changes-4x.html);
  Tika ships an opt-in `legacy-key-migration-filter`.
- `mime_type` is now a hint, not an override. Tika 4 ignores it unless it matches or specializes
  the type detected from the content (TIKA-4825).
- `TikaResponse.language` removed. Tika 4's `/meta` no longer returns it. `/rmeta` and
  `/tika/json` still can, but only with a language-detection filter configured; read
  `tk:detected-language` from `result.data`. 1.0.0 read a plain `language` key, and the detector
  behind it changed too (Tika 4 removes `tika-langdetect-tika`), so values may differ.
- `tika.as_html` and `tika.as_text` now target `/tika/json/html` and `/tika/json/body`, the only
  routes producing the JSON envelope this client parses.
- `tika.as_html.from_file()` and `tika.as_text.from_file()` now read the file into memory rather
  than streaming it, as Tika 4 removed the `/tika/form*` routes. `metadata.from_file()` and
  `rmeta.*.from_file()` are unaffected.

### Added

- `TikaError`, the root of every error this library raises; `HttpStatusError` now subclasses it
- `TikaContainerParseError` and `TikaEmbeddedParseError` for parse failures reported on a `200`
- `TikaResponse.parse_exception`, `.container_exception`, `.embedded_exception`
- `TikaResponse.raise_for_parse_status()` and `TikaResponseList.raise_for_parse_status()`, raising
  on demand the way httpx defers `raise_for_status()`
- `TikaParseErrorGroup`, an `ExceptionGroup` and a `TikaError`, so every failure in an `rmeta`
  call is reported rather than only the first
- `TikaResponseList`, the `rmeta.*` return type, with `has_parse_errors` and `truncated`
- `TikaResponse.truncated`, reporting Tika 4's new `PARTIAL_TIMEOUT`. Not raised, and not part of
  `has_parse_errors`: the content is real but incomplete
- `TikaServerError` and subclasses (`TikaBadRequestError`, `TikaTimeoutError`, `TikaCrashError`,
  `TikaSaturatedError`, `TikaPayloadTooLargeError`, `TikaPartialParseError`) for Tika 4's error
  envelope, all subclassing `HttpStatusError`
- `TikaParseError`, the base for both parse failures above
- `TikaKey.ContainerException`, `TikaKey.EmbeddedException` and `TikaKey.TaskDeadlineReached`
- `TikaResponse` and `TikaResponseList` are now exported from the package root
- `OtherTikaKeys` is now exported, matching its sibling key enums

### Fixed

- `TikaTimeoutError` is raised regardless of status code, matching `TikaCrashError`. Codes that
  are definitive at the protocol level (`400`, `413`, `429`) still take precedence.
- A `422` carrying a `TIMEOUT` or crash envelope is classified as that failure. The envelope is
  only trusted when the body is declared JSON, since a `422` body is extracted document content.
- Parse errors now survive pickling and `deepcopy`, which matters when they cross a process
  boundary inside a `TikaParseErrorGroup`.
- `TikaResponse.parsers` defaults to `[]` instead of raising `KeyError` when Tika could not parse
  at all and returned no `tk:parsed-by`.
- `from_file()` raises `ValueError` for a filename containing a control character, instead of an
  opaque backend-specific error at send time.
- Constructing a `TikaServerError` no longer risks an uncaught `RecursionError` on a deeply
  nested body, and `retry_after` discards non-finite or negative values.
- `TikaServerError` renders a useful `str()` instead of an empty string.
- Integration tests wait longer for tika-server, which starts substantially slower in Tika 4.
- Issue template references Apache Tika Server rather than a copy-pasted Gotenberg reference.

## [1.0.0] - 2026-08-06

### Breaking Change

- `httpx` is no longer installed by default. Install at least one backend via an extra:
  `pip install "tika-client[httpx]"`, `pip install "tika-client[niquests]"`, or
  `pip install "tika-client[requests]"`. The default `backend="auto"` on `TikaClient`
  and `AsyncTikaClient` discovers whichever backend is present at runtime.

### Added

- Pluggable HTTP backend system, decoupling the client from any single HTTP library
- `httpx` as an optional HTTP backend (`pip install tika-client[httpx]`)
- `niquests` as an optional HTTP backend supporting both sync and async (`pip install tika-client[niquests]`)
- `requests` as an optional sync-only HTTP backend (`pip install tika-client[requests]`)
- `backend` parameter on `TikaClient` and `AsyncTikaClient` accepting `"httpx"`, `"niquests"`, `"requests"`, or `"auto"` (default); `"auto"` tries each in order

### Removed

- PyPy 3.10 and PyPy 3.8 dropped from test matrix; `cryptography` 47.0.0 requires PyPy 3.11+

### Security

- All GitHub Actions are now pinned to full commit SHAs instead of tags
- `zizmor` configuration updated to enforce SHA hash-pinning for all actions

## [0.11.0] - 2026-03-11

### Removed

- Support for EoL Python 3.9 has been removed

### Changed

- Various GitHub action dependency updates
- Applies yamlfmt to all files
- `ruff` rule maintenance and additional rules enabled
- Resolved additional `zizmor` reports

### Added

- Validates the changelog format is correct during CI linting job
- Enables `zizmor` for action linting
- Transitions to `prek` over pre-commit
- Testing and official support for Python 3.14

## [0.10.0] - 2025-08-04

### Changed

- Transitions CI to use astral-sh/setup-uv ([#42](https://github.com/stumpylog/tika-client/pull/42))
- Improves the content-disposition header construction ([#43](https://github.com/stumpylog/tika-client/pull/43))
- Bump astral-sh/setup-uv from 5 to 6 ([#44](https://github.com/stumpylog/tika-client/pull/44))

## [0.9.0] - 2025-01-15

### Added

- Allow setting user agent string and provide a default ([#37](https://github.com/stumpylog/tika-client/pull/37))
- Support for async (by [@Goldziher](https://github.com/Goldziher) in [#39](https://github.com/stumpylog/tika-client/pull/39))

### Documentation

- Added contribution guide

## [0.8.1] - 2024-12-17

### Fixed

- Bump pypa/gh-action-pypi-publish from 1.12.2 to 1.12.3, fixing core metadata publishing issue

## [0.8.0] - 2024-12-17

### Breaking Change

- Dropped support for Python 3.8 ([#36](https://github.com/stumpylog/tika-client/pull/36))

### Fixed

- Tests failed when run with Tika v3 ([#28](https://github.com/stumpylog/tika-client/pull/28))
- Relaxed version restriction on `httpx`

### Changed

- Bump pypa/gh-action-pypi-publish from 1.10.2 to 1.12.2 (by [@dependabot](https://github.com/apps/dependabot) in [#33](https://github.com/stumpylog/tika-client/pull/33))
- Bump codecov/codecov-action from 4 to 5 by (by [@dependabot](https://github.com/apps/dependabot)) ([#32](https://github.com/stumpylog/tika-client/pull/32))

### Added

- Integrated Codecov test analytics ([#34](https://github.com/stumpylog/tika-client/pull/34))

## [0.7.0] - 2024-10-09

### Added

- SPDX license headers were added to source files
- Official support and testing for Python 3.13 ([#25](https://github.com/stumpylog/tika-client/pull/25))

### Fixed

- Fixed the README referring to the wrong license text
- Fixed the creation of loggers for the library which were never utilized

### Changed

- Bump pypa/gh-action-pypi-publish from 1.9.0 to 1.10.2 (by [@dependabot](https://github.com/apps/dependabot) in [#22](https://github.com/stumpylog/tika-client/pull/22))
- Update `pre-commit` to 4.0.1 ([#23](https://github.com/stumpylog/tika-client/pull/23))
- Use pytest fixtures effectively ([#24](https://github.com/stumpylog/tika-client/pull/24))
- Use pytest-docker in place of manual Docker ([#26](https://github.com/stumpylog/tika-client/pull/26))

## [0.6.0] - 2024-07-18

### Changed

- Updated development tools
- Bump pypa/gh-action-pypi-publish from 1.8.12 to 1.8.14 (by [@dependabot](https://github.com/apps/dependabot) in [#16](https://github.com/stumpylog/tika-client/pull/16))
- Update development to use `hatch test` and `hatch fmt` ([#17](https://github.com/stumpylog/tika-client/pull/17))
- Included `mypy` typing in the linting checks

### Fixed

- Typo in README codeblock by @Chaostheorie ([#19](https://github.com/stumpylog/tika-client/pull/19))

## [0.5.0] - 2023-11-07

### Added

- Testing on PyPy 3.10
- Testing on released Python 3.12

### Changed

- `.github` and `.docker` folders are no longer included in the source distribution
- Changed the license to Mozilla Public License Version 2.0
- `pypa/gh-action-pypi-publish` updated to v1.8.10
- CI testing now uses the official Apache Tika image (minimal) instead of the paperless-ngx image

## [0.4.0] - 2023-07-27

### Added

- More extensive testing of date and time strings in various formats, including
  [RFC-3339](https://www.ietf.org/rfc/rfc3339.txt), ISO-8061 and things in between

### Changed

- Date parsing is now does not assume a timezone if none is provided (the parsed datetime will be naive)
- `pypa/gh-action-pypi-publish` updated to v1.8.8

## [0.3.0] - 2023-07-19

### Added

- Restricted action permissions to minimal requirements to function
- Github CI also now creates a Github release with sdist, wheel and changelog
- Additional classifiers to the project on PyPI

### Fixed

- Handling of ISO-8061 dates with fractional seconds, which Python doesn't support natively

## [0.2.0] - 2023-06-26

### Fixed

- Handling of filenames in the `Content-Disposition` header with non-ASCII characters

### Changed

- All endpoints now return a `TikaResponse`, which will have many of the common keys parsed into Python
  native data types where possible, based on the list [from the Tika wiki](https://cwiki.apache.org/confluence/display/TIKA/Metadata+Overview).
  If a key is not in the response, the value will be `None`

## [0.1.1] - 2023-06-18

### Fixed

- Fixes an incorrect key when parsing new content types
- Fixed handling of message/rfc822 content type documents

## [0.1.0] - 2023-06-17

### Changed

- Further refinements to the Tika response data models

### Added

- Testing against a .doc format file
- Testing against JPEG and PNG format files

## [0.0.3] - 2023-06-01

### Changed

- The plain text and html versions of the Tika endpoint have been renamed to `as_html` and `as_text`,
  hopefully to make it clearer about the response type
- The plain text and html versions of the recursive endpoint were renamed to `as_html` and `as_text`

### Added

- Optional gzip compression for use when parsing from a buffer instead of a file

### Removed

- The optional dependencies have been removed as Tika does not support HTTP/2 or Brotli

## [0.0.2] - 2023-05-31

### Added

- Print of the Python version to the test coverage running
- Optional dependencies for HTTP/2 and Brotli support in httpx
- `add_headers` to allow users to update the client's headers
- Support for Tika endpoint with a string or byte buffer instead of a file
- Built wheels are now retained for 7 days instead of 90 days

### Fixed

- Reduces the frequency of CodeQL runs

## [0.0.1] - 2023-05-25

### Added

- Support for Tika metadata, tika and recursive metadata endpoints
- Full test coverage
- Full typing
- A changelog
- Comprehensive CI configuration
- Code coverage through codedov.io
- CodeQL scanning

### Fixed

- Fixes the Github Actions test workflow concurrency setting
- Fixes workflow name and file name to reflect what it actually does
