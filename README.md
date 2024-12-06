# Smart Hotel Management System

A comprehensive hotel management system with IoT integration, AI-powered room control, and real-time monitoring capabilities.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the System](#running-the-system)
5. [Testing](#testing)
6. [API Documentation](#api-documentation)
7. [Architecture](#architecture)
8. [Troubleshooting](#troubleshooting)

## System Requirements

- Docker and Docker Compose
- Git
- Bash shell (for Unix-based systems) or Git Bash (for Windows)
- Minimum 4GB RAM
- PostgreSQL client (optional, for direct database access)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/smart-hotel-system.git
cd smart-hotel-system
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Update the `.env` file with your configurations:
```env
# .env.example

# Django Settings
SECRET_KEY=replace_with_your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,[::1]


ROOM_ID=1 

# Postgres Database Settings
POSTGRES_DB=replace_with_your_database_name
POSTGRES_USER=replace_with_your_database_user
POSTGRES_PASSWORD=replace_with_your_database_password

# Database URL
DATABASE_URL=postgres://your_user:your_password@db:5432/your_database

# MQTT Settings
MQTT_BROKER=replace_with_your_mqtt_broker_address
MQTT_PORT=replace_with_your_mqtt_port
MQTT_USERNAME=replace_with_your_mqtt_username
MQTT_PASSWORD=replace_with_your_mqtt_password

# API Base URL
API_BASE_URL='http://localhost:8000'

# Azure OpenAI API Settings
AZURE_OPENAI_API_KEY=replace_with_your_azure_openai_api_key
AZURE_OPENAI_API_VERSION=replace_with_your_azure_openai_api_version
AZURE_OPENAI_ENDPOINT=replace_with_your_azure_openai_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=replace_with_your_azure_openai_deployment_name
AZURE_OPENAI_ASSISTANT_ID=replace_with_your_azure_openai_assistant_id

```

## Configuration

### Docker Setup

The system uses several Docker containers:
- `web`: Django application
- `db`: PostgreSQL database
- `redis`: Redis cache
- `mqtt`: MQTT broker
- `iaq_sensor`: IoT sensor simulator
- `life_being_sensor`: Presence sensor simulator

### Database Configuration

PostgreSQL database settings can be modified in `docker-compose.yml`:
```yaml
db:
  image: postgres:13
  environment:
    - POSTGRES_DB=smart_hotel
    - POSTGRES_USER=postgres
    - POSTGRES_PASSWORD=postgres
```

## Running the System

1. Build and start the containers:
```bash
docker-compose build
docker-compose up -d
```

2. Create initial database migrations:
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

3. Create a superuser:
```bash
docker-compose exec web python manage.py createsuperuser
```

4. Access the application:
- Web Interface: http://localhost:8000
- Admin Interface: http://localhost:8000/admin
- API Documentation: http://localhost:8000/api/
- Chat Interface: http://localhost:8000/chat/

### Starting Individual Services

To start specific services:
```bash
docker-compose up -d web db redis  # Start core services
docker-compose up -d mqtt         # Start MQTT broker
docker-compose up -d iaq_sensor life_being_sensor  # Start sensors
```

## Testing

The project includes a comprehensive test suite. Use the provided `run_tests.sh` script:

### Running All Tests:
```bash
chmod +x run_tests.sh
./run_test.sh
```

### Running Specific Test Categories:
```bash
./run_tests.sh models     # Run model tests
./run_tests.sh api        # Run API tests
./run_tests.sh integration # Run integration tests
./run_tests.sh performance # Run performance tests
./run_tests.sh security   # Run security tests
```

### Test Coverage Report:
After running tests, view the coverage report:
```bash
docker-compose exec web coverage report
```

Detailed HTML coverage report is available at `test-reports/htmlcov/index.html`

## API Documentation

### Core Endpoints:

1. Hotel Management:
```
GET /api/hotels/ - List all hotels
POST /api/hotels/ - Create new hotel
GET /api/hotels/{id}/ - Get hotel details
```

2. Room Management:
```
GET /api/rooms/ - List all rooms
GET /api/rooms/{id}/status/ - Get room status
POST /api/rooms/{id}/control/ - Control room devices
```

3. Sensor Data:
```
GET /api/rooms/{id}/data/iaq/ - Get IAQ sensor data
GET /api/rooms/{id}/data/life-being/ - Get presence data
```

### Authentication:

All API endpoints require authentication except:
- Health check endpoint
- Chat interface endpoints

Include the authentication token in request headers:
```
Authorization: Token your-token-here
```

## Architecture

### System Components:

1. Core Services:
   - Django Web Application
   - PostgreSQL Database
   - Redis Cache
   - MQTT Message Broker

2. IoT Integration:
   - IAQ Sensor Simulator
   - Life Being Sensor Simulator
   - Device Controllers

3. AI Components:
   - OpenAI Integration
   - Azure Services Integration
   - Automated Room Control

### Data Flow:

1. Sensor Data Collection:
   - Sensors publish to MQTT topics
   - Event stream processes messages
   - Data stored in PostgreSQL

2. Room Control:
   - AI controller processes sensor data
   - Automated adjustments based on conditions
   - Manual control through API endpoints

## Troubleshooting

### Common Issues:

1. Database Connection Errors:
```bash
# Check database status
docker-compose ps db
# View database logs
docker-compose logs db
```

2. MQTT Connection Issues:
```bash
# Check MQTT broker status
docker-compose logs mqtt
# Verify MQTT port is open
nc -zv localhost 1883
```

3. Web Application Errors:
```bash
# View Django logs
docker-compose logs web
# Check application status
curl http://localhost:8000/health/
```

### Logs Location:

- Application Logs: `/code/logs/hotel.log`
- MQTT Logs: `/mosquitto/log/mosquitto.log`
- Database Logs: PostgreSQL container logs

### Resetting the System:

To completely reset the system:
```bash
docker-compose down -v  # Remove containers and volumes
docker-compose up -d   # Restart all services
```

For more detailed information, please refer to the specific component documentation in the `docs/` directory.
