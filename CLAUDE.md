# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **File Organizer and Disk Health Manager** desktop application built with Python and PyQt6. The application provides two main functionalities:
1. **File Organization**: Automatically categorizes and organizes files based on their extensions and custom rules
2. **Disk Health Monitoring**: Uses SMART data via smartctl to monitor disk health and performance

## Commands

### Development Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Run tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_smart_parsing.py
```

### External Dependencies
- **smartctl.exe**: Required for disk health monitoring (located in `bin/smartctl.exe`)
- **PyQt6**: Main GUI framework
- **psutil**: System and disk information
- **pySMART**: Python wrapper for SMART data

## Architecture

### Core Structure
```
src/
├── core/                     # Business logic
│   ├── category_manager.py   # File categorization logic and rules
│   ├── disk_manager.py       # Disk detection and management
│   ├── hash_manager.py       # File hashing and duplicate detection
│   ├── workers.py           # Background processing workers
│   └── health_service.py    # SMART data parsing and health analysis
├── gui/                     # User interface
│   ├── main_window.py       # Main application window
│   ├── config_dialog.py     # Category configuration dialog
│   ├── disk_viewer.py       # Disk health visualization
│   └── duplicates_dashboard.py # Duplicate file management
└── utils/                   # Utilities and configuration
    ├── constants.py         # Application constants and modern UI colors
    ├── themes.py           # Modern UI theme management system
    ├── modern_styles.py    # Modern CSS styles with WCAG accessibility
    ├── app_config.py       # Application configuration persistence
    └── smartctl_wrapper.py # SMART data wrapper and parsing
```

### Key Components

#### CategoryManager (`src/core/category_manager.py`)
- Manages file categorization rules and custom extensions
- Supports regex-based custom rules with priority ordering
- Handles nested categories and configuration persistence
- Default categories: MUSICA, VIDEOS, IMAGENES, DOCUMENTOS, PROGRAMAS, CODIGO

#### DiskManager (`src/core/disk_manager.py`)
- Detects available disks and their properties
- Interfaces with smartctl for SMART data collection
- Manages disk health monitoring and alerts

#### Workers (`src/core/workers.py`)
- **AnalysisWorker**: Background file analysis and categorization
- **OrganizeWorker**: Background file moving operations
- Uses Qt signals for progress reporting and UI updates

### Configuration Files

#### Application Configuration
- `app_config.json`: General application settings
- `categories_config.json`: Custom categories and extensions
- `hash_cache.db`: SQLite database for file hash caching

#### SMART Health Monitoring
- Uses `bin/smartctl.exe` to read disk SMART data
- Parses both NVMe and SATA/ATA disk data
- Test fixtures in `tests/fixtures/` for different disk types

### Development Patterns

#### UI Architecture
- Main window uses tabbed interface for different functionalities
- Background workers prevent UI blocking during long operations
- **Modern Theme System**: WCAG 2.1 AA compliant color schemes with 4 available themes
- **Responsive Design**: Optimized button heights (32px) and spacing for desktop usage
- **High Contrast Selection**: Improved table row selection visibility
- Virtualized table models for handling large datasets

#### Data Flow
1. User selects folder for organization
2. AnalysisWorker scans and categorizes files
3. Results displayed in table with preview capabilities
4. OrganizeWorker executes file movements with progress tracking
5. Transaction manager ensures operation atomicity

#### Error Handling
- Comprehensive logging throughout the application
- Transaction rollback for failed file operations
- SMART data parsing with fallback for missing fields

## Testing

### Test Structure
- Unit tests in `tests/` directory
- SMART data parsing tests with JSON fixtures
- Test fixtures for different disk types (NVMe, SATA, HDD)

### Test Data
- `tests/fixtures/nvme_smart.json`: NVMe disk SMART data
- `tests/fixtures/sata_smart.json`: SATA disk SMART data
- `tests/fixtures/hdd_smart.json`: HDD disk SMART data

## Important Notes

### Security Considerations
- File operations use transaction management for safety
- Hash-based duplicate detection to prevent data loss
- Backup recommendations before organizing operations

### Platform Requirements
- Windows-focused (uses WMI for disk detection)
- Requires elevated permissions for some SMART operations
- smartctl.exe must be in PATH or bin/ directory

### Performance Optimizations
- SQLite caching for file hashes to avoid recomputation
- Virtualized table views for large file lists
- Background processing to maintain UI responsiveness

## UI/UX Modern Design System (2025)

### Theme System
- **Modern CSS Architecture**: Complete redesign with professional styling
- **Accessibility Compliance**: WCAG 2.1 AA contrast ratios (4.5:1 minimum)
- **Available Themes**:
  - `Moderno Claro` (default) - Clean light theme with Material Design colors
  - `Moderno Oscuro` - High-contrast dark theme
  - `Profesional Azul` - Corporate blue scheme
  - `Naturaleza Verde` - Calming green palette

### Visual Improvements
- **Button Heights**: Optimized to 32px for desktop usage (down from 44-56px)
- **Table Selection**: High-contrast selection with solid colors instead of transparency
- **Border Radius**: Consistent 6-8px rounded corners throughout
- **Typography**: Segoe UI font family with proper weight hierarchy
- **Micro-interactions**: Smooth 200ms transitions with Material Design easing

### Styling Architecture
- `src/utils/modern_styles.py`: Central CSS generation system
- `src/utils/constants.py`: Modern color palette and UI configuration
- `src/utils/themes.py`: Theme management with fallback handling

### CSS Features
- Gradient backgrounds for primary buttons
- Box shadows for depth perception
- Hover effects with translateY animations
- Focus states with visible borders for accessibility
- Professional dialog styling with rounded corners

## Known Issues

⚠️ **Critical Issues**

### Configuration Dialog Crash
- **Status**: Unresolved
- **Description**: Application crashes when accessing the configuration/options dialog
- **Affected Area**: Settings menu, theme selection
- **Workaround**: None available
- **Investigation**: Theme system initialization may have circular dependencies

### Potential Causes
1. Theme validation issues with saved configurations
2. CSS string formatting errors in dialog styles
3. Missing theme fallbacks in config_dialog.py
4. Import order issues between theme files

### Debug Steps for Future Resolution
1. Check `app_config.json` for invalid theme names
2. Verify all theme references use exact names from `THEMES` dictionary
3. Test theme loading in isolation: `ThemeManager.get_css_styles("Moderno Claro")`
4. Review config_dialog.py imports and theme application order

## Troubleshooting

### Theme-Related Issues
- Verify theme names match exactly in `app_config.json`
- Default theme is `"Moderno Claro"` (no emojis)
- Clear app configuration if themes appear corrupted
- Check console output for theme fallback warnings

### UI Performance
- Button heights are optimized for desktop (32px standard)
- Table selection uses solid colors for better visibility
- CSS animations are limited to 200ms for smooth performance