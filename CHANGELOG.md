# Changelog

All notable changes to the KernelCI Staging Control application will be documented in this file.

## [Unreleased]

### Added
- **Staging Run Cancellation**: Added ability to cancel running staging runs
  - Cancel button visible to run owners, admins, and maintainers
  - Automatically cancels GitHub workflows via GitHub Actions API
  - Properly marks all pending/running steps as skipped or cancelled
- **Kernel Tree "None" Option**: Added option to skip kernel tree update entirely
  - New "None (Skip kernel tree update)" option in staging trigger form
  - Orchestrator skips kernel tree step when "none" is selected
  - UI displays "None (Skipped)" badge for clarity
- **AJAX Staging Triggers**: Converted staging run form to AJAX
  - Better error handling and user feedback
  - Loading states with progress indicators
  - No page refresh required
- **Changelog Viewer**: Added changelog modal accessible from navigation
  - Fetches and displays CHANGELOG.md content
  - Simple markdown-to-HTML conversion for formatting
  - Accessible via "Changelog" link next to profile dropdown
- **Database Migration System**: Automatic schema migrations on startup
  - Detects and adds missing database columns automatically
  - Future-proof system for easy schema updates
  - Clear logging of migration progress and status
- **Improved Message Types**: Separated informational messages from errors
  - New `info_message` field for warnings, skip reasons, and notifications
  - `error_message` field reserved for actual errors only
  - Better visual distinction with appropriate styling (yellow vs red)

### Changed
- **GitHub Workflow Manager**: Enhanced with workflow cancellation capability
  - Added `cancel_workflow_run()` method with proper error handling
  - Constructor now stores repo and workflow as instance variables
  - Better handling of GitHub API responses (202 Accepted status)
- **Orchestrator Logic**: Improved handling of cancelled and skipped runs
  - Skips processing of cancelled staging runs entirely
  - Better keyword handling for kernel tree selection ("auto", "none", specific trees)
  - Enhanced validation and error reporting
- **Form Handling**: Replaced problematic form-based submission with clean AJAX API
  - New `/api/staging/trigger` endpoint accepting JSON payloads
  - Removed complex form parsing and debugging code
  - Cleaner separation between UI and API logic

### Fixed
- **Configuration Issues**: Resolved missing TOML dependency and settings keys
  - Hardcoded settings keys to eliminate config file dependency issues
  - Added missing `toml` dependency to requirements.txt
  - Simplified configuration by removing unnecessary `[settings_keys]` section
- **Form Parsing Problems**: Fixed kernel tree selection issues
  - Eliminated mysterious form data parsing problems
  - Proper handling of "none" vs "None" string confusion
  - Clear validation and error messages
- **Missing Imports**: Added missing `datetime` import in main.py for cancellation functionality

### Technical Improvements
- **Database Constraints**: Enhanced single-run enforcement and conflict resolution
- **Error Handling**: Improved HTTP status codes and JSON error responses
- **UI/UX**: Better visual feedback with loading states, progress indicators, and status badges
- **Code Organization**: Cleaner separation of concerns between form handling and business logic