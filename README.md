
# MIGHT NEED TO re-clone or reset their local repos ON PORTABLE LAPTOP 
 - 20250802 


# WORK LOG (MAJOR STEPS)

UPDATE RUNNING AND BUILDING SECTIONS SEPARATELY 

THIS IS JUST FOR FOLLOWING WHERE WE ARE IN THE PROJECT 

## Late-July 

* Scoped out project, via a few LLM sessions (see work & projects folder "20250620-LLM for customized NB email blasts by segment")

* Got set up to point of opening a NB database snapshot and generated email open frequency 
  * src\email_open_frequency.py


## Early-August 

### Side project to automate path updates 

To get familiar with NB APIs (and to get some tasks off my plate), 
want to set up scripts to automate the path updates 

#### 20250807 

Prompt to shift over from Claude.AI to VSCode's AI chat 

  OK, I'm picking things up with you mid-project. Let's try to catch you up to speed. 
  I'm developing a script that works with NationBuilder's API. 
  The intention is to have it run on Google Cloud Functions (using a timer trigger), 
  but I also want to be able to develop, test, and run locally (that's where we at now, no Google Cloud Function aspec yet). 
  It will update the "path step" for certain people in NationBuilder (path steps are a NationBuilder feature we can review later), however, currently we're just finding the correct people in NationBuilder, we haven't gotten to writing data to NationBuilder yet. 

  The script is composed of modules. 
  The main file: 
  nb_path_updates\nb_path_nightly\main.py 
  Utilities modules: 
  nb_path_updates\nb_path_nightly\utils\logging_utils.py
  nb_path_updates\nb_path_nightly\utils\reporting_utils.py
  First of ~6 modules that will be used to update the various people: 
  nb_path_updates\nb_path_nightly\filters\clickers.py

  What I currently need help with is to get the automatic token refresh set up. I will give you additional info about what we've got there so far, but I wanted to give you the background first. Are you clear on the background and can we proceed to the token auto-refresh, or should we review the background and context more?  I want to make sure you are very clear on the overall project before proceeding. 

Follow up prompt: 

  OK, I've attached NationBuilder's API Authentication Guide, which I've been following. 
  I've completed up through step 5 in Setting Up OAuth 2.0 Authentication, but i'm having trouble wiht the Refresh Token Flow section. 
  These are the files that I've set up so far: 
  src\nb_api_client.py
  src\oauth_token_exchanger.py
  These are the names of the references in my .env
  NB_NATION_SLUG=...
  NB_PA_ID=...
  NB_PA_SECRET=...
  NB_PA_REDIRECT_URI=http://localhost:8000/callback
  NB_PA_TOKEN=...
  NB_PA_TOKEN_REFRESH=...
  Can you help me test the token refresh? I'm new to APIs, tokens, and authentification, and I'd like to get the token refresh aspect set up in a solid and dependable way. I'd like whatever we set up now to be able to run on both the local testing and on the Google Cloud Functions when we're ready to shift things over to there. 

____________________________________________
____________________________________________
--> CURRENT STATUS <--
For the clickers module, got the script successfully 
- finding people wiht a tag 
- adding them to a new list (with unique slug)
- updating them to the relevant path step 

--> NEXT STEPS: CLEAN, UNDERSTAND, TEST <--
- review clickers, nb_api_client, and main to understand what's going on 
- clean up clickers, nb_api_client, and main
- Set up testing 
- assess if should add docker before Google Cloud 

--> DEPLOY TO CLOUD <--
- get running on Google Cloud 
  - need to add and connect storage probably 
- set up saved filter & auto tag
  - check autotag timing and have timer trigger set appropriately 
- add modules for each path 

--> LATER STEPS <--
- monthly updates to path names as separate set of modules 
- consider email open frequency auto-path 
  - would need to automatically grab and parse database snapshot 
  - might want to control auto-path from list (one list per step) so nightly runs could ensure steps are correct (without having to run full databse parsing and assessment, which would probably run weekly or monthly, given the level of compute required)
____________________________________________
____________________________________________




# RUNNING 

## Venv 

* Virtual Environment and dependencies 
  * `.\.venv\Scripts\Activate.ps1` 
  * `pip install -r requirements.txt` 

## Docker (for ...)

* For Docker 
  * Docker Desktop needs to be running 
  * Start the database: `docker-compose up -d`
    * Pro tip: `docker-compose up -d` is safe to run multiple times - it only starts containers that aren't already running.
  * When you're done working: `docker-compose down`
    * This stops the containers but keeps your data 

### Temp notes 

Sample database extraction powershell commands 

  docker exec campaign_buddy_postgres pg_dump -U dev_user -d campaign_buddy_ai -t nbuild_larouchepac.mailing_events_opened --data-only --column-inserts > data/mailing_events_opened.sql

  docker exec campaign_buddy_postgres psql -U dev_user -d campaign_buddy_ai -c "\COPY (SELECT * FROM nbuild_larouchepac.mailing_events_sent LIMIT 100) TO STDOUT WITH CSV HEADER" > data/mailing_events_sent_sample.csv

nbuild_larouchepac.signups 


## NationBuilder API 

* ... 


# STEP-BY-STEP BUILDING 

## Repo 

* New GitHub repo `campaign_buddy_ai`
  * Created folder structure and files following AI suggestions
  * Create virtual environment 
    * `python -m venv .venv` 

## Python Dependencies 

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

## Docker 

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

## Restore NB Snapshot 

* Restore a NB database snapshot 
  * Copy the dump file into the container
    * `docker cp .\data\backup-for-larouchepac20250728-50530-q0c394_ campaign_buddy_postgres:/tmp/backup.dump` 
      * This copied your local backup file (backup-for-larouchepac20250728-50530-q0c394_) into the running Docker container named campaign_buddy_postgres, placing it at /tmp/backup.dump inside the container.
  * Create required extensions 
      * According to ChatGPT, the NB backup "expects the shared_extensions schema (with types like hstore and citext) to exist, but it is missing in your database. This is common for NationBuilder or Rails/Postgres apps that use extensions."
    * `docker exec -it campaign_buddy_postgres psql -U dev_user -d campaign_buddy_ai -c "CREATE SCHEMA IF NOT EXISTS shared_extensions;"`
    * `docker exec -it campaign_buddy_postgres psql -U dev_user -d campaign_buddy_ai -c "CREATE EXTENSION IF NOT EXISTS hstore SCHEMA shared_extensions;"`
    * `docker exec -it campaign_buddy_postgres psql -U dev_user -d campaign_buddy_ai -c "CREATE EXTENSION IF NOT EXISTS citext SCHEMA shared_extensions;"`
    * `docker exec -it campaign_buddy_postgres psql -U dev_user -d campaign_buddy_ai -c "CREATE EXTENSION IF NOT EXISTS pg_trgm SCHEMA shared_extensions;"`
  * Restore from inside the container (with 2nd option to ignore ownership issues)
    * `docker exec -it campaign_buddy_postgres pg_restore -U dev_user -d campaign_buddy_ai -v /tmp/backup.dump`
    * `docker exec -it campaign_buddy_postgres pg_restore -U dev_user -d campaign_buddy_ai -v --no-owner --no-privileges /tmp/backup.dump`
      * This ran the pg_restore command inside the campaign_buddy_postgres container, using the dev_user user to restore the database dump (/tmp/backup.dump) into the campaign_buddy_ai database. The -v flag gave you verbose output about the restore process.
  * Export database tables 
    * `docker exec -it campaign_buddy_postgres psql -U dev_user -d campaign_buddy_ai -c "\dt nbuild_larouchepac.*" > tables.txt` 

## NationBuilder API Authentification 

Following "API Authentication Guide" 
    `https://intercom.help/3dna/en/articles/9903805-api-authentication-guide`

* In the Nation's settings --> developer, register an app 
  * Save 
    * OAuth client ID 
    * OAuth client secret
    * OAuth callback URL 
* Authenticate with NationBuilder API using OAuth 2.0 
  * Compose URL with relevant info to get short-lived code
    * `https://[YOUR_NATION].nationbuilder.com/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&response_type=code`
  * Exchange the authorization code for an access token 
    * `nationbuilder_token_exchange.py`
  * Saved 
    * access_token
    * refresh_token 
  * Access tokens are good for 24 hours, then need to use refresh token

## NB API Access Scripts 

* src\nb_api_client.py 
  * Built by Claud.AI, handles: 
  * Authentication: 
    * Handles OAuth 2.0, including automatic refresh of access tokens using the refresh token when the API returns a 401 Unauthorized.
    * Updates .env with new tokens when running locally; uses environment variables in cloud deployments.
  * API Requests: 
    * Wraps NationBuilder endpoints for signups, tags, taggings, paths, path steps, and path journeys, making it easy to fetch and update people and their path steps.
  * Pagination: 
    * Supports fetching large datasets across multiple pages.
  * Error Handling: 
    * Raises custom exceptions and logs errors for failed requests or authentication issues.

* src\oauth_token_exchanger.py 
  * Built by Claud.ai, only for manual refresh of tokens 
  * A utility script that helps you manually obtain fresh NationBuilder API tokens using the OAuth 2.0 authorization code flow in a step by step process. 

## NationBuilder Paths Scripts

* Using NB API to automate the path updates 
* The script and it's modules are under nb_path_updates\ 
* nb_path_updates\nb_path_nightly 
  * For updating people onto the relevant path steps each night 
    * Relies on existing NB saved filters and their tags (outlined below)


### NationBuilder Filters and Auto-Tags 

* Using saved filters and autotags
  * Due to the limits of NB API (limits not fully confirmed)
  * Will need to run nightly 
    * Saved filters grab anyone with relevant activity in last 24 hours, and tag them 
    * Script will then find people with those tags, and add them to the appropriate path step 
* For clickers path 
  * Saved filter, 
  * Auto-Tag, zi-c-24h


# BASIC GITHUB SETUP NOTES: 

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
