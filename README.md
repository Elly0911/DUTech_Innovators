Run these commands when you first clone the repository:
cd <your folder loaction>

1. Create a virtual environment
python -m venv flaskappenv

2. Activate the virtual environment (Windows)
flaskappenv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. Apply new database migrations (if changes exist)
flask db init (only run this if the migrations folder is not there when you first clone, otherwise don’t run)
flask db upgrade

Update the requirements.txt file when you install new packages
pip freeze > requirements.txt
