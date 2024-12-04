#!/bin/bash

echo "Starting Smart Hotel System Tests..."

# Create a log file
LOG_FILE="test_run_$(date '+%Y%m%d_%H%M%S').log"
echo "Logging output to: $LOG_FILE"

# Ensure services are running
docker-compose up -d

# Wait for web service to be ready
echo "Waiting for web service..."
sleep 10

# Apply migrations
docker-compose exec -T web python manage.py migrate

# Run tests and capture output
docker-compose exec -T web python test_smart_hotel.py 2>&1 | tee -a "$LOG_FILE"

# Check test result
TEST_RESULT=${PIPESTATUS[0]}

# Show logs if there are errors
if [ $TEST_RESULT -ne 0 ]; then
    echo "Tests failed. Showing last 50 lines of logs..."
    docker-compose logs --tail=50 web | tee -a "$LOG_FILE"
    echo "Full logs available in: $LOG_FILE"
fi

# Exit with the test result
exit $TEST_RESULT