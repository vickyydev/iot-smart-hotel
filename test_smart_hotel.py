import requests
import json
import time
from datetime import datetime, timedelta
import logging
import sys
from random import uniform

# Enhanced logging configuration
log_file = f"smart_hotel_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SmartHotelTester:
    def __init__(self, base_url="http://web:8000"):  # Changed from localhost to web
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.room_ids = []
        self.room_device_map = {}  # Map room_id to device_id

    def _make_request(self, method, endpoint, data=None):
        """Make HTTP request and handle response"""
        url = f"{self.api_url}/{endpoint}"
        logger.info(f"Making {method} request to: {url}")
        if data:
            logger.info(f"Request data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url)
            elif method == 'POST':
                response = requests.post(url, json=data)
            elif method == 'PUT':
                response = requests.put(url, json=data)
            elif method == 'DELETE':
                response = requests.delete(url)
            
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code in [200, 201, 204]:  # Added 204 for DELETE
                if method != 'DELETE':  # DELETE typically returns no content
                    response_data = response.json()
                    logger.info(f"Response data: {json.dumps(response_data, indent=2)}")
                    return response_data
                return True
            else:
                logger.error(f"Request failed: {response.status_code}")
                logger.error(f"Response content: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return None

    def setup_test_data(self):
        """Create test hotel, floors, and rooms"""
        logger.info("Setting up test data...")
        
        try:
            # Get list of existing hotels
            existing_hotels = self._make_request('GET', 'hotels/')
            if existing_hotels and 'results' in existing_hotels:
                for hotel in existing_hotels['results']:
                    if hotel['name'] == 'Test Hotel':
                        self._make_request('DELETE', f"hotels/{hotel['id']}/")
                        logger.info(f"Deleted existing test hotel with ID: {hotel['id']}")
        except Exception as e:
            logger.warning(f"Cleanup failed: {str(e)}")

        # Create hotel
        hotel_data = {
            'name': 'Test Hotel',
            'address': '123 Test Street'
        }
        hotel = self._make_request('POST', 'hotels/', hotel_data)
        if not hotel:
            raise Exception("Failed to create hotel")
        
        hotel_id = hotel['id']
        logger.info(f"Created hotel with ID: {hotel_id}")

        # Clear existing data
        self.room_ids = []
        self.room_device_map = {}

        # Create floors (2 floors)
        floor_data = []
        for floor_num in range(1, 3):  # Create floors 1 and 2
            floor = self._make_request('POST', f'hotels/{hotel_id}/floors/', {
                'hotel': hotel_id,
                'number': floor_num,
                'description': f'Floor {floor_num} - Test Hotel'
            })
            if not floor:
                raise Exception(f"Failed to create floor {floor_num}")
            floor_data.append((floor['id'], floor_num))
            logger.info(f"Created floor {floor_num} with ID: {floor['id']}")
            
            time.sleep(1)

        # Create rooms for each floor
        for floor_id, floor_num in floor_data:
            for room_num in range(1, 6):  # 5 rooms per floor
                room_number = f"{floor_num}{str(room_num).zfill(2)}"  # e.g., 101, 102, 201, 202
                
                room_data = {
                    'floor': floor_id,
                    'number': room_number,
                    'is_occupied': False
                }
                
                room = self._make_request('POST', 
                    f'hotels/{hotel_id}/floors/{floor_id}/rooms/', 
                    room_data
                )
                if not room:
                    raise Exception(f"Failed to create room {room_number}")
                
                room_id = room['id']
                self.room_ids.append(room_id)
                logger.info(f"Created room {room_number} with ID: {room_id}")
                # Create AC device first
                device_data = {
                    'room': room_id,
                    'device_type': 'AC',
                    'name': f'AC Unit - Room {room_number}',
                    'status': 'ON',
                    'settings': {
                        'mode': 'AUTO',
                        'temperature': 24.0,
                        'fan_speed': 1
                    }
                }

                device = self._make_request('POST', 
                    f'hotels/{hotel_id}/floors/{floor_id}/rooms/{room_id}/devices/', 
                    device_data
                )
                if not device:
                    raise Exception(f"Failed to create AC device for room {room_number}")

                device_id = device['id']
                self.room_device_map[room_id] = device_id
                logger.info(f"Created AC device for room {room_number}")

                # Create AC Control with explicit settings
                ac_control_data = {
                    'temperature': 24.0,
                    'mode': 'AUTO',
                    'fan_speed': 1,
                    'humidity_control': True,
                    'target_humidity': 50
                }

                # Make the request to create AC control
                ac_control = self._make_request('POST', 
                    f'rooms/{room_id}/devices/{device_id}/control/', 
                    ac_control_data
                )

                if not ac_control:
                    logger.warning(f"AC Control creation might have failed for room {room_number}")

                # Add delay between operations
                time.sleep(1)

        # Store first room and device IDs for tests
        if self.room_ids:
            self.room_id = self.room_ids[0]
            self.device_id = self.room_device_map.get(self.room_id)
        else:
            raise Exception("No rooms were created successfully")

        return True

    def test_room_status(self):
        """Test room status endpoint"""
        logger.info("\nTesting room status...")
        status = self._make_request('GET', f'rooms/{self.room_id}/status/')
        if status:
            logger.info("Room status retrieved successfully")
            logger.info(json.dumps(status, indent=2))
            return True
        return False

    def test_ac_control(self):
        """Test AC control functionality"""
        logger.info("\nTesting AC control...")
        
        # Test different AC modes
        test_cases = [
            {'temperature': 23, 'mode': 'COOL', 'fan_speed': 2},
            {'temperature': 25, 'mode': 'AUTO', 'fan_speed': 1},
            {'temperature': 26, 'mode': 'FAN', 'fan_speed': 3}
        ]

        for case in test_cases:
            logger.info(f"Testing AC settings: {case}")
            # Use the correct URL pattern
            response = self._make_request(
                'POST',
                f'rooms/{self.room_id}/devices/{self.device_id}/control/',
                case
            )
            if response:
                logger.info("AC control successful")
            else:
                logger.error("AC control failed")
                return False
            time.sleep(1)  # Wait between tests

        return True

    def test_occupancy_response(self):
        """Test system response to occupancy changes"""
        logger.info("\nTesting occupancy response...")
        
        success = True
        for room_id in self.room_ids:
            # Simulate occupancy with random variations
            presence_data = {
                'room': room_id,
                'presence_detected': True,
                'motion_level': round(uniform(60, 100)),  # Random motion level between 60-100
                'presence_state': 'occupied',
                'sensitivity': round(uniform(0.7, 0.9), 1)  # Random sensitivity between 0.7-0.9
            }
            
            response = self._make_request('POST', f'rooms/{room_id}/data/life-being/', presence_data)
            if not response:
                logger.error(f"Failed to simulate occupancy for room {room_id}")
                success = False
            
            # Add small delay between requests
            time.sleep(0.5)
            
            # Check room status after occupancy
            status = self._make_request('GET', f'rooms/{room_id}/status/')
            if status:
                logger.info(f"Room {room_id} status after occupancy:")
                logger.info(json.dumps(status, indent=2))

        return success

    def test_environmental_response(self):
        """Test system response to environmental changes"""
        logger.info("\nTesting environmental response...")
        
        success = True
        for room_id in self.room_ids:
            # Add some random variation to make data more realistic
            iaq_data = {
                'room': room_id,
                'temperature': round(uniform(24.0, 28.0), 1),
                'humidity': round(uniform(55, 75)),
                'co2': round(uniform(600, 1000)),
                'tvoc': round(uniform(0.3, 0.8), 2),
                'pm25': round(uniform(10, 20)),
                'noise': round(uniform(35, 45)),
                'illuminance': round(uniform(300, 500))
            }
            
            response = self._make_request('POST', f'rooms/{room_id}/data/iaq/', iaq_data)
            if not response:
                logger.error(f"Failed to simulate environmental conditions for room {room_id}")
                success = False
            
            # Add small delay between requests
            time.sleep(0.5)
            
            # Check room status after environmental change
            status = self._make_request('GET', f'rooms/{room_id}/status/')
            if status:
                logger.info(f"Room {room_id} status after environmental change:")
                logger.info(json.dumps(status, indent=2))

        return success

    def test_energy_monitoring(self):
        """Test energy monitoring functionality"""
        logger.info("\nTesting energy monitoring...")
        
        # Get energy report
        report = self._make_request('GET', f'rooms/{self.room_id}/energy-report/')
        if report:
            logger.info("Energy report retrieved successfully:")
            logger.info(json.dumps(report, indent=2))
            return True
        return False

    def run_all_tests(self):
        """Run all tests in sequence"""
        logger.info("=" * 80)
        logger.info("Starting Smart Hotel system tests...")
        logger.info("=" * 80)

        try:
            # Setup
            if not self.setup_test_data():
                raise Exception("Test data setup failed")
            
            # Run tests
            tests = [
                self.test_room_status,
                self.test_ac_control,
                self.test_occupancy_response,
                self.test_environmental_response,
                self.test_energy_monitoring
            ]

            results = []
            for test in tests:
                logger.info("\n" + "=" * 40)
                logger.info(f"Running test: {test.__name__}")
                try:
                    result = test()
                    results.append((test.__name__, result))
                except Exception as e:
                    logger.error(f"Test {test.__name__} failed: {str(e)}")
                    results.append((test.__name__, False))

            # Print summary
            logger.info("\nTest Summary:")
            for test_name, result in results:
                status = "PASSED" if result else "FAILED"
                logger.info(f"{test_name}: {status}")

        except Exception as e:
            logger.error(f"Testing failed: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        tester = SmartHotelTester()
        tester.run_all_tests()
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        sys.exit(1)