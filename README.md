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

* ... 
  * `.\.venv\Scripts\Activate.ps1` 
  * `pip install -r requirements.txt` 


# STEP-BY-STEP BUILDING 

* New GitHub repo 
  * Created folder structure and files following AI suggestions
  * Create virtual environment 
    * `python -m venv .venv` 
  * Install core python dependencies
    * Via `requirements.txt`
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