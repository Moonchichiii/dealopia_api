#!/bin/sh

set -e

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create cache tables
echo "Setting up cache tables..."
python manage.py createcachetable

# Load initial data if specified
if [ "$LOAD_FIXTURES" = "true" ]; then
    echo "Loading initial data..."
    python manage.py loaddata initial_data
fi

# Start server
echo "Starting server..."
exec "$@"