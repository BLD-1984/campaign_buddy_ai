Let's go! 


campaign_buddy_ai/
├── .venv/
├── data/
│   ├── .gitkeep
├── src/
│   ├── __init__.py
│   ├── main.py  # FastAPI app
│   ├── db.py    # Database connection logic
├── tests/
│   ├── __init__.py
├── .env
├── .gitignore
├── requirements.txt
├── README.md


├── Dockerfile   # For containerizing the app
├── docker-compose.yml  # For local Postgres



# RUNNING 

* Virtual Environment and dependencies 
  * `.\.venv\Scripts\Activate.ps1` 
  * `pip install -r requirements.txt` 

* For Docker 
  * Docker Desktop needs to be running 
  * Start the database: `docker-compose up -d`
    * Pro tip: `docker-compose up -d` is safe to run multiple times - it only starts containers that aren't already running.
  * When you're done working: `docker-compose down`
    * This stops the containers but keeps your data 



Sample database extraction powershell commands 

  docker exec campaign_buddy_postgres pg_dump -U dev_user -d campaign_buddy_ai -t nbuild_larouchepac.mailing_events_opened --data-only --column-inserts > data/mailing_events_opened.sql

  docker exec campaign_buddy_postgres psql -U dev_user -d campaign_buddy_ai -c "\COPY (SELECT * FROM nbuild_larouchepac.mailing_events_opened LIMIT 100) TO STDOUT WITH CSV HEADER" > data/mailing_events_opened_sample.csv




# STEP-BY-STEP BUILDING 

* New GitHub repo `campaign_buddy_ai`
  * Created folder structure and files following AI suggestions
  * Create virtual environment 
    * `python -m venv .venv` 

* Install core python dependencies (using a `requirements.txt`)
  * `fastapi` 
    * Web framework to build the API for your app, handling requests to generate segment-specific emails.
  * `uvicorn[standard]` 
    * Server to run your FastAPI app, enabling it to handle HTTP requests locally or in production.
  * `asyncpg`
    * Python library for async database access to Postgres, used to extract NationBuilder email and engagement data efficiently.
  * `python-dotenv`
    * Loads environment variables from .env (e.g., database credentials) for secure configuration.
  * `sqlalchemy[asyncio]`
    * ORM library for Python to interact with Postgres asynchronously, simplifying data extraction and management.

* Set up Docker 
  * Install Docker Windows app 
    * `https://www.docker.com/products/docker-desktop/`
    * Keep all default settings
    * It will ask to enable WSL 2 - say Yes
    * Needed to also install Windows Subsystem for Linux 
  * Create a simple Docker Compose file to run PostgreSQL locally
    * Create Docker Compose File in root directory `docker-compose.yml`
    * In powershell run `docker-compose up -d` in order to: 
      * Download PostgreSQL 16 (first time only)
      * Start the database in the background
      * Create a database called `campaign_buddy_ai`
      * To verify `docker-compose ps`
    * Update `.env` file to match the Docker database 
      * ... 
    * Check status with the powershell commands: 
      * `docker-compose up -d`
      * `docker-compose ps`

* Explore a NB database snapshot 
  * Copy the dump file into the container
    * `docker cp .\data\backup-for-larouchepac20250728-50530-q0c394_ campaign_buddy_postgres:/tmp/backup.dump` 
      * This copied your local backup file (backup-for-larouchepac20250728-50530-q0c394_) into the running Docker container named campaign_buddy_postgres, placing it at /tmp/backup.dump inside the container.
  * Restore from inside the container (with 2nd option to ignore ownership issues)
    * `docker exec -it campaign_buddy_postgres pg_restore -U dev_user -d campaign_buddy_ai -v /tmp/backup.dump`
    * `docker exec -it campaign_buddy_postgres pg_restore -U dev_user -d campaign_buddy_ai -v --no-owner --no-privileges /tmp/backup.dump`
      * This ran the pg_restore command inside the campaign_buddy_postgres container, using the dev_user user to restore the database dump (/tmp/backup.dump) into the campaign_buddy_ai database. The -v flag gave you verbose output about the restore process.
  * Export database tables 
    * `docker exec -it campaign_buddy_postgres psql -U dev_user -d campaign_buddy_ai -c "\dt nbuild_larouchepac.*" > tables.txt` 





# BASIC GITHUB SETUP: 

## Create new repo
* Create local folder 
* Create basic files
    * README.md 
    * .gitignore 
    * requirements.txt 
* Create local repo 
    * git init 
* Create repo on GitHub 
* Connect reop 
    * git remote add origin [...] 
* Update GitHub 
    * git add .
    * git commit -m "new" 
    * git push --set-upstream origin master 
* Create virtual environment 
    * python -m venv venv 
* Activate venv
    * .\venv\Scripts\Activate.ps1 
* Install required packages 
    * pip install -r requirements.txt

## Sync existing repo 
* Navigate to / open VSCode to parent folder for repo 
    * git clone [...] 
* Create virtual environment 
    * python -m venv venv 
* Activate venv
    * .\venv\Scripts\Activate.ps1 
* Install required packages 
    * pip install -r requirements.txt
