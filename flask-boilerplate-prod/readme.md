# Boilerplate code to start a Flask project

Basic functionalities and dependencies for flask Projects.

## Technical Details

- Python 3.10 - preferable
- Flask 2.3.2
- Postgresql (Database) 12.12
- SQLAlchemy (ORM for the project)
  - All the SQL queries are written with SQLAlchemy in mind
  - Has great performance compared to Django's default ORM
- Alembic
  - DB migration tool, to use with SQLAlchemy
  - To generate migrations from models & reflect those migrations in the database
- Swagger
  - For documenting and testing APIs

## Directory Structure

- `apps/`
  - Contains all the logic of components in separate directories related to app.
  - Static files (CSS, JS, & Plugins (Bootstrap4, SB-Admin2))
  - Models' logic
  - Templates (layouts & pages for email's)
  - Views (For url redirection and their logic)
- `config/`
  - Contains sample_config.yml file
- `migrations/versions/`
  - Contains all the Alembic migrations
  - File Naming Convention: `revisionID_description.py`
- `providers/`
  - `mail.py` contains mail sending logic.
- `workers/`
  - Contains a workers according to tasks.
- `manage.py`
  - Contains seeder command for generating admin.
  - Run this command to create super_admin : `python manage.py create_user`

## Installation Instructions

### Create Virtual Environment

- After cloning the repository, execute following commands

```
cd flask_boiler_plate

# Create & Activate virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install all the packages
pip install --upgrade pip
pip install -r requirements.txt
```

- If you get an error regarding any requirement while installing requirements. Comment that requirement from requirements.txt.
- Manually install requirement without mentioning version.
- continue installing requirements
- uncomment requirement from requirements.txt file.

### Configuring the Database

- Run following commands to install postgresql in the system:

```
sudo apt-get update
sudo apt-get install python3-pip python3-dev libpq-dev postgresql postgresql-contrib
```

#### Changing default isolation_level :

- In alembic migration transaction is committed only after all version files implemented there can be some scenario in which you are altering table and reading that table data that will lead to deadlock issue.
- we can overcome by setting isolation level to autocommit.
- Put below line in config.yml file for updating isolation_level to autocommit.
- In SQLAlchemy, the isolation_level parameter is used to specify the isolation level of a database transaction.
- Isolation levels control the degree to which one transaction is isolated from the effects of other transactions.
- Isolation levels do not affect whether or not a transaction is automatically committed.

```
SQLALCHEMY_ENGINE_OPTIONS : {'isolation_level': 'AUTOCOMMIT'}
```

#### Create the database

```
# Login to postgres session
sudo -u postgres psql

# Create a database with below command.
CREATE DATABASE 'boiler-plate';

# Press \q to exit the postgres session
\q
```

- run migrations using `flask db upgrade`

#### Create config.yml file

- After installing requirements.txt create file `config/config.yml` file copying from `config/config.sample.yml`.
  - Edit `config.yml` by updating it with your secret key, and other database credentials.
  - Else ask for already updated `config.yml` file from another team member.

## Setup Redis

- For starting redis server run below commands:

```
wget http://download.redis.io/releases/redis-6.0.6.tar.gz
tar xzf redis-6.0.6.tar.gz
cd redis-6.0.6
make
```

- Run the Redis server in a separate terminal window on the default port with the command `src/redis-server` from the directory where it's installed.

- For starting RQ Worker run below commands:

```
rqscheduler -i INTERVAL (How often the scheduler checks for new jobs to add to the queue in seconds.)
example :  rqscheduler -i 1 -v

Refer this article for more details: https://github.com/rq/rq-scheduler

rq worker QUEUE_NAME --with-scheduler
```

## Adding Rate limiting

- For adding rate limiting you have to create instance of Flask-Limiter in Application init file.

```
limiter = Limiter(app=app, key_func=, strategy=, key_prefix=, storage_uri=)
```

- Must have arguments while creating Instance:
  - key_func : A callable that returns the domain to rate limit (e.g. username, ip address etc)
  - strategy : The rate limiting strategy to use. we can use one of fixed-window, fixed-window-elastic-expiry, or moving-window.
  - key_prefix : Prefix that is prepended to each stored rate limit key and app context global name.
  - storage_uri : A storage location conforming to the scheme in storage-scheme.
- You can use it as a decorator on API logic method as below:

```
 @limiter.limit(limit_value='1/ 30 second', key_func=lambda: request.get_json(force=True).get('email_id'))
```

- You can find more details in this link : https://flask-limiter.readthedocs.io/en/stable/index.html

### Alembic - Generating Migrations

- Once models are changed for any component, run following commands to create its migrations file & reflect it into the database

```
flask db migrate -m "Write description of migration here" --rev-id=REVISION_ID
```

<!--alembic revision --autogenerate -m "Write description of migration here"-->

- Rename file generated inside `migrations/versions/` with the following naming convention: `revisionID_description`

  - ex: `0005_add_country_code_in_org_table.py`
  - Also update the Revision ID `revision` & `down_revision` in the generated file to match the version number

- Run `flask db upgrade` to have this new migration reflected in the database.

- Note: Once you delete all the tables (i.e, when freshly migrating to DB), run `flask db upgrade` to have all the changes reflected in the database.

##### Important alembic commands for reference

- To rollback 1 migration: `flask db downgrade -1`
- Downgrade to specific migration: `flask db downgarde <revision>`

## Code Flow

### Swagger Documentation

- url for swagger is http://localhost:5000/api-docs
- Whenever you make any changes in API or DB Schema You must have to make changes in `app/static/swagger_json/swagger.json` file

### Pre-Commit Hook

Refer this link to know more -- `https://github.com/Edugem-Technologies/gists/blob/prod/python-pre-commit-hooks.md`

- Open below link to get basic understanding about pre-commit hooks :
  `https://ljvmiranda921.github.io/notebook/2018/06/21/precommits-using-black-and-flake8/`
- The pre-commit hook is run first, before you even type in a commit message.
- It's used to inspect the snapshot that's about to be committed, to see if you've forgotten something, to make sure tests run, or to examine whatever you need to inspect in the code.
- Run `pip install pre-commit` to install the pre-commit package manager.
- Create a configuration file named `.pre-commit-config.yaml`
- You can generate a very basic configuration using `pre-commit sample-config`
- Run `pre-commit install` to set up the git hook scripts.
- To check all files for newly added hooks run `pre-commit run --all-files`
- Open `https://pre-commit.com/hooks.html` this URL to read about more useful hooks.

### Helpers

- The helper folder in our 'app' of root contains the utility.py file for functions like generating random numbers, decode and encode functions etc
- The constants.py file has all the enumerations and functions to get there names and values
- It also contains custom decorations

### Workers

- The workers folder in our root contains files related to specific tasks.
- Email workers have email related functions

### App logs

- The logging output goes into the app.log file whose path depends on LOG_FILE_PATH of the config file
### Audit Logs
- For any database action(Create, Update, Delete), a new row is created in audit_log table.
- Audit event listens for any action/event performed in the table and store its information.
- When model that inherits audit log undergoes add/delete/update, its audit log is created with following information:
    user_id = id of user who hit the api , this will be blank if no user is found in token in headers of the request.
    table_name = Table name on which any action performed
    object_id = object_id in the table, which is effected by action.
    action = create, update, delete.
    state_before = value of the object before performing action.
    state_after = value of the object after performing action.
    method = api request method (GET, POST, PUT, DELETE, OPTIONS etc.)
    url = api url which initiated database action.
    headers = headers with api request.
    body = body data with api call.
    args = arguments with api call.
    ip = ip of the system which calls the api.
NOTE: To enable Audit Log on any table we need to inherit AuditEvent class in model. [e.g. class User(AuditableEvent, db.Model):]
### Models and Relations

- User:
  - It contains details of each User and their personal details.

## Branch Naming Convention

- Refer to the link below to understand how to name a branch
  - https://bitbucket.org/edugemservice/workspace/snippets/Mzy8GL

Branches 'master' and 'development' are no commit branches, which means one cannot directly commit and push to them.

## Unit Testing

- We have used pytest for writing test cases.
- All Unit Tests are under the `tests` directory.
- We need to create the test db in the postgres, default config name is: `project_name_test` which can be updated as well.
- Tables will be created in the db on each time we run testing setup and will be cleared once done.

#### conftest.py file

- This file contains logic for creating temporary DB and initializing app for testing.
- We have initialized org_admin_client and super_admin_client in this file which can be used in all test cases.
- To preform the data cleanup, write the cleanup logic after the yield in client function of conftest.py
- All the configuration or generic test functions need to be written in conftest.py.

#### Other files

- we have created separate file per module for writing their test cases as below:
- 1. `test_user.py` : This file contains all test cases related to user onboarding process.

#### To add pytest in pre-commit add below code in `pre-commit-config.yaml`

```
  - repo: local
  hooks:
    - id: pytest-check
      name: pytest-check
      entry: pytest
      language: system
      pass_filenames: false
      always_run: true
```
