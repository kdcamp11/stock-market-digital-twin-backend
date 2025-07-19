# Data Ingestion Layer for Stock Market Digital Twin

## Overview
This module fetches historical and live price data for a list of stock symbols, stores it locally in SQLite, and updates automatically on a schedule.

## Setup
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Edit `config.yaml` to set your symbols, date range, interval, and update schedule.

3. Run the ingestion script:
   ```
   python ingestion.py
   ```

## Files
- `ingestion.py`: Main ingestion logic.
- `scheduler.py`: Schedules automatic updates.
- `storage.py`: Handles local database storage.
- `config.yaml`: Configuration file.
