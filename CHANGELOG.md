# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
