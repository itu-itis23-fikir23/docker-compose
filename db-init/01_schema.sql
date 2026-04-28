-- Auto-run by PostgreSQL on first startup (mounted to /docker-entrypoint-initdb.d)

CREATE TABLE IF NOT EXISTS sales (
    id          SERIAL PRIMARY KEY,
    product     VARCHAR(100) NOT NULL,
    category    VARCHAR(50)  NOT NULL,
    quantity    INTEGER      NOT NULL,
    unit_price  NUMERIC(10,2) NOT NULL,
    sale_date   DATE         NOT NULL,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sales_category ON sales(category);
CREATE INDEX IF NOT EXISTS idx_sales_date     ON sales(sale_date);
