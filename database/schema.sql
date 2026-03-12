CREATE TABLE IF NOT EXISTS exchange_rates (
    base_currency TEXT NOT NULL,
    target_currency TEXT NOT NULL,
    rate_date TEXT NOT NULL,
    exchange_rate REAL NOT NULL,
    frequency TEXT NOT NULL DEFAULT 'D',
    source TEXT NOT NULL,
    loaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (base_currency, target_currency, rate_date, frequency)
);
