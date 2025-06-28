# Stock Data Management and Screening System

运行时请键入如下命令：  python src/main.py
python -m src.main

A Python-based system for downloading, managing, and screening stock data using Tushare API, SQLite, and Tkinter GUI.

## Features
- Download daily stock data (price, volume, PE, PB, market value) from Tushare.
- Store data in SQLite databases.
- Screen stocks based on technical indicators (MA, RSI, volume).
- User-friendly GUI for data updates and screening.
- Logging for errors and progress.

## Directory Structure
stock_system/
├── config/
│   └── settings.ini
├── data/
│   ├── daily_data.db
│   ├── financial_data.db
│   ├── watchlist.csv
│   ├── results/
│   └── logs/
├── src/
│   ├── config_manager.py
│   ├── data_acquisition.py
│   ├── data_storage.py
│   ├── technical_analyzer.py
│   ├── stock_screener.py
│   ├── gui.py
│   └── main.py
├── README.md
└── requirements.txt


## Setup
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt

Configure Tushare API:
Obtain a Tushare API token from Tushare.
Update config/settings.ini with your token.
Prepare Watchlist:
Create a data/watchlist.csv with a column ts_code listing stock codes (e.g., 002292.SZ).
Run the System:
bash

Collapse

Wrap

Copy
python src/main.py
Usage
Update Daily Data: Downloads and stores daily stock data for new trading days.
Update Financial Data: Placeholder for future implementation.
Screen Stocks: Select a watchlist CSV and run technical screening. Results are saved in data/results/.
Exit: Closes the application.
Requirements
Python 3.8+
Libraries: pandas, tushare, sqlite3, tkinter
Notes
Ensure a stable internet connection for Tushare API access.
Check data/logs/ for error logs if issues occur.
Financial data update is not implemented in this version.
text

Collapse

Wrap

Copy

#### 10. requirements.txt
pandas>=1.5.0
tushare>=1.2.0

text

Collapse

Wrap

Copy

*Note*: `sqlite3` and `tkinter` are part of Python's standard library, so they are not listed.

#### 11. data/watchlist.csv (Example)

```csv
ts_code
002292.SZ
000733.SZ
002465.SZ
...
Note: This is a sample based on the provided watchlist. Users should create their own or use the provided list.