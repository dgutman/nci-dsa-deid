#!/bin/sh

# Source the .env file to export environment variables
# if [ -f /app/.env ]; then
#   export $(cat /app/.env | xargs)
# fi
source .env

# Run the application
exec python app.py