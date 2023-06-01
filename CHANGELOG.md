# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
