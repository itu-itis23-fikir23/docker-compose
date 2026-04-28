# Docker Compose — Applied Data Engineering Demo

A small, reproducible data engineering stack orchestrated by **Docker Compose**:
PostgreSQL, pgAdmin, and a Python ETL container that loads a CSV file into the
database and reports aggregated revenue per category.

---

## 1. What is this tool?

**Docker Compose** is the official tool from Docker for defining and running
multi-container applications. You describe every service, network, and volume
your application needs in a single `docker-compose.yml` file, and a single
command (`docker compose up`) builds the images, creates the network, and
starts the containers in the right order. It turns "follow ten install
guides" into "clone the repo and run one command".

---

## 2. Prerequisites

| Requirement   | Version                               |
| ------------- | ------------------------------------- |
| OS            | Linux, macOS, or Windows (WSL2)       |
| Docker Engine | 20.10 or newer                        |
| Docker Compose| v2 (bundled with Docker Desktop / `docker compose` plugin on Linux) |
| Free ports    | `5432` (Postgres), `5050` (pgAdmin)   |
| Disk space    | ~500 MB for the images                |

Verify your installation:

```bash
docker --version
docker compose version
```

You should see Docker `20.10+` and Compose `v2.x`.

---

## 3. Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/<your-username>/docker-compose-demo.git
cd docker-compose-demo
```

### Step 2 — Create your `.env` file

```bash
cp .env.example .env
```

The defaults work out of the box; edit `.env` only if ports `5432` or `5050`
are already in use on your machine.

### Step 3 — Build and start the stack

```bash
docker compose up --build
```

Compose will:

1. Build the Python ETL image from `app/Dockerfile`
2. Pull the official `postgres:16-alpine` and `dpage/pgadmin4:8.12` images
3. Create a private network `de_network`
4. Start `postgres` first, wait until its healthcheck passes, then start
   `pgadmin` and run the `etl_app` container

To run in the background instead, add `-d`:

```bash
docker compose up --build -d
```

---

## 4. Running the example

The ETL container runs automatically when the stack starts up. To run it
again on demand (for example after editing `data.csv`):

```bash
docker compose run --rm etl_app
```

To open a SQL shell directly against the database:

```bash
docker compose exec postgres psql -U de_user -d de_demo -c "SELECT COUNT(*) FROM sales;"
```

To use pgAdmin in the browser:

1. Open <http://localhost:5050>
2. Log in with `[email protected]` / `admin`
3. Right-click **Servers → Register → Server**
4. **General** tab → Name: `de_demo`
5. **Connection** tab:
   - Host: `postgres`  (the service name on the Docker network)
   - Port: `5432`
   - Username: `de_user`
   - Password: `de_password`

To stop everything:

```bash
docker compose down
```

To stop and also delete the database volume (full reset):

```bash
docker compose down -v
```

---

## 5. Expected output

When the ETL container runs successfully you should see something like this in
the Compose logs:

```
dc_etl_app  | [ETL] Loaded 15 rows from /app/data.csv.
dc_etl_app  | [ETL] Connected to PostgreSQL on attempt 1.
dc_etl_app  | [ETL] Inserted 15 rows into sales.
dc_etl_app  |
dc_etl_app  | [ETL] Revenue by category
dc_etl_app  | ------------------------------------------------------------
dc_etl_app  | Category            Lines     Units         Revenue ($)
dc_etl_app  | ------------------------------------------------------------
dc_etl_app  | Electronics             7        40            7,213.92
dc_etl_app  | Furniture               4         8            1,576.96
dc_etl_app  | Stationery              2        65              672.10
dc_etl_app  | Kitchen                 2        25              424.75
dc_etl_app  | ------------------------------------------------------------
dc_etl_app  | [ETL] Done.
dc_etl_app exited with code 0
```

You can verify the same data in pgAdmin or via `psql`:

```bash
docker compose exec postgres psql -U de_user -d de_demo \
  -c "SELECT category, SUM(quantity * unit_price)::numeric(10,2) AS revenue
       FROM sales GROUP BY category ORDER BY revenue DESC;"
```

A screenshot of the expected pgAdmin view is in `screenshots/pgadmin.png`.

---

## 6. Project structure

```
docker-compose-demo/
├── docker-compose.yml      # Service / network / volume definitions
├── .env.example            # Template for environment variables
├── .gitignore
├── README.md
├── db-init/
│   └── 01_schema.sql       # Auto-run by Postgres on first startup
└── app/
    ├── Dockerfile          # Python 3.12-slim image for the ETL service
    ├── requirements.txt    # psycopg2-binary
    ├── data.csv            # 15 sample sales rows
    └── etl.py              # Loads the CSV and prints a summary report
```

---

## 7. How it maps to the seven core course tools

| Course tool   | How this project uses it                                                   |
| ------------- | -------------------------------------------------------------------------- |
| **Docker**    | Every service runs in a container; Compose builds on top of Docker.        |
| **PostgreSQL**| The `postgres` service is the analytical destination for the ETL job.     |
| **pgAdmin**   | The `pgadmin` service connects to Postgres on the shared Docker network.  |
| Apache NiFi / Airflow | Could be added as additional services in the same `docker-compose.yml` to schedule the ETL — that is exactly the scaling story Compose is designed for. |
| Elasticsearch / Kibana | Same pattern: drop them in as new services and they share the network with the rest. |

In other words, every stack you have built in class so far has been *one
service*; Docker Compose is the layer that lets you wire them together.

---

## 8. AI usage disclosure

I used **Anthropic Claude** as an assistant during this assignment. Specifically:

- **Drafting the `docker-compose.yml`**: I asked Claude to produce a first
  draft of the multi-service Compose file with healthchecks and a shared
  network. I then read the [official Compose specification](https://docs.docker.com/compose/compose-file/)
  and adjusted the `depends_on: condition: service_healthy` block, the
  volume bind-mount paths, and the named-volume names myself.
- **Writing the Python ETL script**: I asked Claude for a connection-retry
  pattern with `psycopg2`. I rewrote the bulk-insert section to use
  `execute_values` after reading the psycopg2 docs.
- **README structure**: I asked Claude to suggest a readable section layout
  for the assignment requirements; the technical content and commands were
  verified by actually running the stack on my machine.
- **Slide deck**: I drafted the slide outline with Claude, then trimmed and
  rewrote the speaker notes in my own voice.

No AI-generated content was submitted without being read, executed, and
verified end-to-end.

---

## 9. Troubleshooting

| Symptom                                            | Fix                                                             |
| -------------------------------------------------- | --------------------------------------------------------------- |
| `port is already allocated`                        | Change `POSTGRES_PORT` or `PGADMIN_PORT` in `.env`              |
| `etl_app` exits with `Postgres not ready`          | Run `docker compose up --build` again — Compose will reuse the existing healthy DB |
| pgAdmin can't connect using `localhost`            | Inside Docker the host is `postgres`, **not** `localhost`       |
| Want a clean slate                                 | `docker compose down -v` removes the volume                     |

---

## 10. References

- Docker Compose documentation — <https://docs.docker.com/compose/>
- Compose file reference — <https://docs.docker.com/compose/compose-file/>
- Official PostgreSQL image — <https://hub.docker.com/_/postgres>
- Official pgAdmin image — <https://hub.docker.com/r/dpage/pgadmin4>
- psycopg2 documentation — <https://www.psycopg.org/docs/>
