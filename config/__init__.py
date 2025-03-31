import os


class Config:
    DB_PATHS = {
        'daily': 'data/daily.db',
        'portfolio': 'data/portfolio.db'
    }
    API_KEYS = {
        'tushare': os.getenv('TUSHARE_TOKEN')
    }
