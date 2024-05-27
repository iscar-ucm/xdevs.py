# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Added

- Add real-time simulation capabilities, including input and output handlers
- CI/CD pipeline for automated testing

### Changed

- Transitioned from setup.py to pyproject.toml for package configuration
- Updated dependencies to latest versions
- deltcon now does not accept any input arguments
- All abstract classes are now defined in the `abc` module
- All plugin factories are now defined in the `factory` module
- Minimum Python version is now 3.9

### Removed

- Faulty parallel simulator
