# ees33-backend
Repository for backend of EES 23 website 

For starting the project first time :
1. Clone the repo in which you have to work in your system.
2. Create or do your work in other branch with relevant name
3. After completing your work, commit your changes and push them
4. Create a pull request (PR)

Setting up the project(Backend) :

1. Initial setup:
install virtual environment
`python -m venv venv`
activate virtual environment
linux:`source venv/bin/activate`  
windows: `./venv/Scripts/activate`
2. install dependencies
`pip install -r requirements/dev.txt`

3. apply migrations: `python manage.py migrate`
4. Collect static files : `python manage.py collectstatic`
5. Start the development server using `python manage.py runserver`

For Uptading work after some PRs are merged :
1. Commit your changes (if any)
2. Pull from the main branch (always)

General Rules : 
1. For APIs, test it with all possible test case, so it will not cause any future problems.
2. Always inform Ankur bhaiya after adding a pull request and get it reviewed by him.
