# Scraper Modifications Summary

## Overview
The scraper has been successfully modified to remove Redis queue operations and API endpoint calls, replacing them with local file storage in both TXT and JSON formats.

## Status: ✅ COMPLETED

### Changes Made:

#### 1. New Files Created
- **`backend/scraper/src/infrastructure/files/report_json_saver.py`**
  - Handles JSON file creation and saving
  - Saves files to `./reports/json/` directory without date-based subdirectories
  - Converts Publication entities to Prisma-compatible JSON format
  - Provides statistics for saved JSON files

- **`backend/scraper/src/application/usecases/save_publications_to_files.py`**
  - New use case that saves publications to both TXT and JSON files
  - Replaces the Redis-based SavePublicationsUseCase

#### 2. Files Removed
- **`backend/scraper/src/application/usecases/save_publications.py`** - Old Redis-based save use case
- **`backend/scraper/src/cli/redis_cli.py`** - Redis CLI management tool

#### 3. Files Modified
- **`backend/scraper/src/application/services/scraping_orchestrator.py`**
  - Changed from `SavePublicationsUseCase` to `SavePublicationsToFilesUseCase`
  - Updated statistics to use file-based stats instead of queue stats

- **`backend/scraper/src/infrastructure/web/dje_scraper_adapter.py`**
  - Added `ReportJsonSaver` instance
  - Modified all publication processing sections to save both TXT and JSON files

- **`backend/scraper/src/main.py`**
  - Removed all PublicationWorker references
  - Removed Redis-related imports
  - Updated logging messages to reflect file-based storage
  - Fixed scheduler method calls

- **`backend/scraper/src/infrastructure/config/settings.py`**
  - Added `SchedulerSettings` class for scheduler configuration
  - Added scheduler settings to main Settings class

#### 4. JSON File Structure
```json
{
  "process_number": "1234567-89.2023.8.26.0000",
  "publication_date": "2023-11-13",
  "availability_date": "2023-11-14",
  "authors": ["João da Silva"],
  "defendant": "Instituto Nacional do Seguro Social - INSS",
  "lawyers": [{"name": "Dr. Pedro", "oab": "123456/SP"}],
  "gross_value": 150000,  // in cents
  "net_value": 120000,    // in cents
  "interest_value": 20000, // in cents
  "attorney_fees": 10000,  // in cents
  "content": "Full publication content...",
  "status": "NOVA",
  "scraping_source": "DJE-SP",
  "caderno": "3",
  "instancia": "1",
  "local": "Capital",
  "parte": "1",
  "extraction_metadata": {},
  "scraping_execution_id": null,
  "created_at": "2023-11-14T10:30:00.000Z",
  "updated_at": "2023-11-14T10:30:00.000Z"
}
```

#### 5. File Storage Structure
- **TXT Files**: `reports/txt/YYYY-MM-DD/{process_number}.txt`
- **JSON Files**: `reports/json/{process_number}.json`
- **File Naming**: Both TXT and JSON files use only the process number as filename (with `/` and `.` replaced by `_`)

#### 6. File Naming Convention
- Both TXT and JSON files now use the same naming pattern
- Filename format: `{process_number}.{extension}`
- Example: Process `1234567-89.2023.8.26.0000` becomes `1234567-89_2023_8_26_0000.txt` and `1234567-89_2023_8_26_0000.json`
- Special characters (`/` and `.`) are replaced with underscores (`_`)
- **Filename Format**: Process number with special characters replaced (e.g., `1234567-89_2023_8_26_0000.json`)

## Current Status
- ✅ Scraper is running successfully in Docker container
- ✅ Scheduled for daily execution at 06:00 starting from 2025-03-17
- ✅ All Redis and API dependencies removed
- ✅ Publications saved locally in both TXT and JSON formats
- ✅ JSON format is Prisma-compatible for future database integration

## Testing
The scraper can be tested using:
```bash
# Dry run (no data saved)
docker exec juscash-scraper python -m src.cli.commands run --max-pages 1 --dry-run

# Actual run
docker exec juscash-scraper python -m src.cli.commands run --max-pages 1
```

## Notes
- The scraper maintains backward compatibility with existing TXT file functionality
- JSON files contain all the same information as TXT files but in a structured format
- The scraper no longer requires Redis or API endpoints to function
- All publications are stored locally and can be processed later when needed