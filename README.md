Run these commands when you first clone the repository:

1. Ensure you are in the correct directory:
   
    cd your-folder-location
    
2. Create a virtual environment:
   
    python -m venv flaskappenv

3. Activate the virtual environment:

   flaskappenv\Scripts\activate

4. Install dependencies:

   pip install -r requirements.txt

5. Apply new database migrations (if changes exist):

    flask db init (Only run flask db init if the migrations folder is missing when you first clone the repository. Otherwise, skip this step and just run flask db upgrade.)
  
    flask db upgrade

Update the requirements.txt file when you install new packages:

  pip freeze > requirements.txt
