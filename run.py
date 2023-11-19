import os
from dotenv import load_dotenv
from webapp.app import create_app

# Assume a default environment
env = os.environ.get('ENVIRONMENT', 'development')

# Load the corresponding .env file
if env == 'development':
    dotenv_path = '.env'

load_dotenv(dotenv_path)


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
