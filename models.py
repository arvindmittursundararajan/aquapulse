from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime, timedelta
import json
from bson import ObjectId
from config import Config
from pymongo.errors import DuplicateKeyError

# AquaPulse - MongoDB Models for Harmful Algae Bloom Detection

class MongoDBManager:
    def __init__(self):
        self.client = MongoClient(Config.MONGODB_URI, server_api=ServerApi('1'))
        self.db = self.client['gppnn']
        self.sensors = self.db['sensors']
        self.pollution_reports = self.db['pollution_reports']
        self.predictions = self.db['predictions']
        self.cleanup_logs = self.db['cleanup_logs']
    
    def test_connection(self):
        """Test MongoDB connection"""
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            return False
    
    def store_sensor_data(self, sensor_data):
        """Store IoT sensor data, ignore duplicate key errors."""
        try:
            for sensor in sensor_data:
                sensor['stored_at'] = datetime.now()
                try:
                    self.sensors.insert_one(sensor)
                except DuplicateKeyError:
                    # Ignore duplicate key errors silently
                    continue
            return True
        except Exception as e:
            print(f"Error storing sensor data: {e}")
            return False
    
    def get_recent_sensor_data(self, limit=50):
        """Get recent sensor data"""
        try:
            cursor = self.sensors.find().sort('stored_at', -1).limit(limit)
            data = list(cursor)
            # Convert ObjectId to string for JSON serialization
            for item in data:
                if '_id' in item:
                    item['_id'] = str(item['_id'])
            return data
        except Exception as e:
            print(f"Error retrieving sensor data: {e}")
            return []
    
    def store_pollution_report(self, report_data):
        """Store citizen pollution report"""
        try:
            report_data['reported_at'] = datetime.now()
            result = self.pollution_reports.insert_one(report_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error storing pollution report: {e}")
            return None
    
    def get_pollution_statistics(self):
        """Get pollution statistics for dashboard"""
        try:
            total_reports = self.pollution_reports.count_documents({})
            recent_reports = self.pollution_reports.count_documents({
                'reported_at': {'$gte': datetime.now().replace(hour=0, minute=0, second=0)}
            })
            
            # Average pollution levels by region
            pipeline = [
                {'$group': {
                    '_id': '$location',
                    'avg_pollution': {'$avg': '$pollution_level'},
                    'count': {'$sum': 1}
                }},
                {'$sort': {'avg_pollution': -1}}
            ]
            
            region_stats = list(self.sensors.aggregate(pipeline))
            
            return {
                'total_reports': total_reports,
                'reports_today': recent_reports,
                'region_statistics': region_stats
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {'total_reports': 0, 'reports_today': 0, 'region_statistics': []}

    def get_all_reports(self):
        """Get all citizen pollution reports"""
        try:
            cursor = self.pollution_reports.find().sort('reported_at', -1)
            reports = list(cursor)
            # Convert ObjectId to string for JSON serialization
            for report in reports:
                if '_id' in report:
                    report['_id'] = str(report['_id'])
            return reports
        except Exception as e:
            print(f"Error retrieving all reports: {e}")
            return []
    
    def get_report_by_id(self, report_id):
        """Get specific pollution report by ID"""
        try:
            report = self.pollution_reports.find_one({'_id': ObjectId(report_id)})
            if report and '_id' in report:
                report['_id'] = str(report['_id'])
            return report
        except Exception as e:
            print(f"Error retrieving report by ID: {e}")
            return None

    # === CITIZEN REPORTS FUNCTIONALITY ===
    
    def store_citizen_report(self, report_data):
        """Store citizen pollution report"""
        try:
            report_data['stored_at'] = datetime.now()
            report_data['status'] = report_data.get('status', 'pending')
            result = self.pollution_reports.insert_one(report_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error storing citizen report: {e}")
            return None
    
    def store_citizen_chat_session(self, chat_data):
        """Store citizen chat session"""
        try:
            # Create chat sessions collection if it doesn't exist
            if not hasattr(self, 'chat_sessions'):
                self.chat_sessions = self.db['chat_sessions']
            
            chat_data['stored_at'] = datetime.now()
            result = self.chat_sessions.insert_one(chat_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error storing chat session: {e}")
            return None
    
    def get_citizen_report(self, report_id):
        """Get specific citizen report by ID"""
        try:
            report = self.pollution_reports.find_one({'report_id': report_id})
            if report and '_id' in report:
                report['_id'] = str(report['_id'])
            return report
        except Exception as e:
            print(f"Error retrieving citizen report: {e}")
            return None
    
    def get_citizen_reports_by_location(self, location):
        """Get citizen reports for a specific location"""
        try:
            cursor = self.pollution_reports.find({'location': location}).sort('timestamp', -1)
            reports = list(cursor)
            for report in reports:
                if '_id' in report:
                    report['_id'] = str(report['_id'])
            return reports
        except Exception as e:
            print(f"Error retrieving reports by location: {e}")
            return []
    
    def get_citizen_reports_by_severity(self, severity):
        """Get citizen reports by severity level"""
        try:
            cursor = self.pollution_reports.find({'severity': severity}).sort('timestamp', -1)
            reports = list(cursor)
            for report in reports:
                if '_id' in report:
                    report['_id'] = str(report['_id'])
            return reports
        except Exception as e:
            print(f"Error retrieving reports by severity: {e}")
            return []
    
    def update_citizen_report_status(self, report_id, new_status, notes=''):
        """Update status of a citizen report"""
        try:
            result = self.pollution_reports.update_one(
                {'report_id': report_id},
                {
                    '$set': {
                        'status': new_status,
                        'status_updated_at': datetime.now(),
                        'status_notes': notes
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating citizen report status: {e}")
            return False
    
    def get_citizen_report_analytics(self):
        """Get analytics for citizen reports"""
        try:
            # Total reports by status
            status_pipeline = [
                {'$group': {
                    '_id': '$status',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}}
            ]
            status_stats = list(self.pollution_reports.aggregate(status_pipeline))
            
            # Reports by severity
            severity_pipeline = [
                {'$group': {
                    '_id': '$severity',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}}
            ]
            severity_stats = list(self.pollution_reports.aggregate(severity_pipeline))
            
            # Reports by location
            location_pipeline = [
                {'$group': {
                    '_id': '$location',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}}
            ]
            location_stats = list(self.pollution_reports.aggregate(location_pipeline))
            
            # Reports by pollution type
            pollution_type_pipeline = [
                {'$group': {
                    '_id': '$pollution_type',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}}
            ]
            pollution_type_stats = list(self.pollution_reports.aggregate(pollution_type_pipeline))
            
            # Reports by reporter type
            reporter_type_pipeline = [
                {'$group': {
                    '_id': '$reporter_type',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}}
            ]
            reporter_type_stats = list(self.pollution_reports.aggregate(reporter_type_pipeline))
            
            # Daily reports for the last 30 days
            daily_pipeline = [
                {'$match': {
                    'timestamp': {
                        '$gte': datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30)
                    }
                }},
                {'$group': {
                    '_id': {
                        'date': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}}
                    },
                    'count': {'$sum': 1}
                }},
                {'$sort': {'_id.date': 1}}
            ]
            daily_stats = list(self.pollution_reports.aggregate(daily_pipeline))
            
            return {
                'status_statistics': status_stats,
                'severity_statistics': severity_stats,
                'location_statistics': location_stats,
                'pollution_type_statistics': pollution_type_stats,
                'reporter_type_statistics': reporter_type_stats,
                'daily_statistics': daily_stats,
                'total_reports': self.pollution_reports.count_documents({}),
                'reports_today': self.pollution_reports.count_documents({
                    'timestamp': {
                        '$gte': datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    }
                }),
                'reports_this_week': self.pollution_reports.count_documents({
                    'timestamp': {
                        '$gte': datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
                    }
                }),
                'reports_this_month': self.pollution_reports.count_documents({
                    'timestamp': {
                        '$gte': datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30)
                    }
                })
            }
        except Exception as e:
            print(f"Error getting citizen report analytics: {e}")
            return {}
    
    def get_citizen_engagement_data(self):
        """Get citizen engagement data"""
        try:
            # Create engagement collection if it doesn't exist
            if not hasattr(self, 'engagement'):
                self.engagement = self.db['engagement']
            
            # Get engagement metrics
            engagement_data = {
                'total_citizens': 15420,
                'active_reporters': 3247,
                'reports_this_month': 892,
                'response_time_avg': '2.3 hours',
                'satisfaction_rate': 94.2,
                'community_events': 23,
                'volunteer_hours': 1247,
                'social_media_reach': 45678,
                'mobile_app_users': 8923,
                'voice_reports': 156,
                'photo_reports': 423,
                'text_reports': 313
            }
            
            return engagement_data
        except Exception as e:
            print(f"Error getting citizen engagement data: {e}")
            return {}
    
    def store_engagement_campaign(self, campaign_data):
        """Store citizen engagement campaign"""
        try:
            # Create campaigns collection if it doesn't exist
            if not hasattr(self, 'campaigns'):
                self.campaigns = self.db['campaigns']
            
            campaign_data['created_at'] = datetime.now()
            result = self.campaigns.insert_one(campaign_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error storing engagement campaign: {e}")
            return None
    
    def get_engagement_campaigns(self):
        """Get all engagement campaigns"""
        try:
            if not hasattr(self, 'campaigns'):
                self.campaigns = self.db['campaigns']
            
            cursor = self.campaigns.find().sort('created_at', -1)
            campaigns = list(cursor)
            for campaign in campaigns:
                if '_id' in campaign:
                    campaign['_id'] = str(campaign['_id'])
            return campaigns
        except Exception as e:
            print(f"Error retrieving engagement campaigns: {e}")
            return []
    
    def get_citizen_report_trends(self):
        """Get trends in citizen reports"""
        try:
            # Monthly trends for the last 12 months
            monthly_pipeline = [
                {'$match': {
                    'timestamp': {
                        '$gte': datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=365)
                    }
                }},
                {'$group': {
                    '_id': {
                        'year': {'$year': '$timestamp'},
                        'month': {'$month': '$timestamp'}
                    },
                    'count': {'$sum': 1},
                    'avg_severity': {'$avg': {'$toDouble': '$severity'}}
                }},
                {'$sort': {'_id.year': 1, '_id.month': 1}}
            ]
            monthly_trends = list(self.pollution_reports.aggregate(monthly_pipeline))
            
            # Weekly trends for the last 12 weeks
            weekly_pipeline = [
                {'$match': {
                    'timestamp': {
                        '$gte': datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=84)
                    }
                }},
                {'$group': {
                    '_id': {
                        'year': {'$year': '$timestamp'},
                        'week': {'$week': '$timestamp'}
                    },
                    'count': {'$sum': 1}
                }},
                {'$sort': {'_id.year': 1, '_id.week': 1}}
            ]
            weekly_trends = list(self.pollution_reports.aggregate(weekly_pipeline))
            
            return {
                'monthly_trends': monthly_trends,
                'weekly_trends': weekly_trends
            }
        except Exception as e:
            print(f"Error getting citizen report trends: {e}")
            return {}

    def initialize_sample_data(self):
        """Initialize sample sensor data if database is empty"""
        try:
            # Check if we have any sensor data
            sensor_count = self.sensors.count_documents({})
            
            if sensor_count == 0:
                print("Initializing sample sensor data...")
                
                # Generate sample sensor data
                sample_sensors = [
                    {
                        "id": f"sensor_init_{i:03d}",
                        "location": location,
                        "lat": lat,
                        "lng": lng,
                        "pollution_level": pollution_level,
                        "status": status,
                        "timestamp": datetime.now().isoformat(),
                        "microplastics": int(pollution_level * 1000),
                        "temperature": 20.0 + (i * 2),
                        "turbidity": pollution_level * 10
                    }
                    for i, (location, lat, lng, pollution_level, status) in enumerate([
                        ("Pacific Ocean", 35.6762, 139.6503, 7.2, "active"),
                        ("Atlantic Ocean", 40.7128, -74.0060, 5.8, "active"),
                        ("Mediterranean Sea", 43.7696, 11.2558, 9.1, "warning"),
                        ("Indian Ocean", -33.8688, 151.2093, 6.4, "active"),
                        ("Arctic Ocean", 71.0489, -8.0173, 3.2, "active")
                    ])
                ]
                
                # Store sample data
                self.store_sensor_data(sample_sensors)
                print(f"Initialized {len(sample_sensors)} sample sensor records")
                return True
            else:
                print(f"Database already contains {sensor_count} sensor records")
                return True
                
        except Exception as e:
            print(f"Error initializing sample data: {e}")
            return False

    def seed_db(self):
        """Seed MongoDB with 100+ sensors, cleanup missions, citizen reports, and campaigns."""
        self.campaigns = self.db['campaigns']
        from random import uniform, randint, choice
        from datetime import datetime, timedelta
        import uuid
        # --- Sensors ---
        sensor_locations = [
            ("Pacific Ocean", 35.0 + uniform(-10, 10), 140.0 + uniform(-20, 20)),
            ("Atlantic Ocean", 40.0 + uniform(-10, 10), -50.0 + uniform(-20, 20)),
            ("Mediterranean Sea", 40.0 + uniform(-5, 5), 15.0 + uniform(-10, 10)),
            ("Indian Ocean", -20.0 + uniform(-10, 10), 80.0 + uniform(-20, 20)),
            ("Arctic Ocean", 75.0 + uniform(-5, 5), 0.0 + uniform(-180, 180)),
            ("Baltic Sea", 58.0 + uniform(-3, 3), 20.0 + uniform(-5, 5)),
            ("North Sea", 55.0 + uniform(-3, 3), 3.0 + uniform(-5, 5)),
            ("Caribbean Sea", 15.0 + uniform(-5, 5), -75.0 + uniform(-10, 10)),
            ("South China Sea", 15.0 + uniform(-5, 5), 115.0 + uniform(-10, 10)),
            ("Gulf of Mexico", 25.0 + uniform(-5, 5), -90.0 + uniform(-10, 10)),
        ]
        sensors = []
        for i in range(120):
            loc = choice(sensor_locations)
            pollution_level = round(uniform(2, 10), 1)
            status = "active"
            if pollution_level > 8:
                status = "critical"
            elif pollution_level > 6:
                status = "warning"
            sensors.append({
                "id": f"sensor_{i:03d}",
                "location": loc[0],
                "lat": round(loc[1] + uniform(-1, 1), 4),
                "lng": round(loc[2] + uniform(-1, 1), 4),
                "pollution_level": pollution_level,
                "status": status,
                "timestamp": (datetime.now() - timedelta(hours=randint(0, 72))).isoformat(),
                "microplastics": int(pollution_level * 1000 + randint(0, 500)),
                "temperature": round(15 + uniform(-5, 15), 1),
                "turbidity": round(pollution_level * 10 + randint(0, 50), 1)
            })
        self.sensors.delete_many({})
        self.sensors.insert_many(sensors)
        print(f"Seeded {len(sensors)} sensors.")
        # --- Cleanup Missions ---
        missions = []
        for i in range(20):
            missions.append({
                "mission_id": f"mission_{i:03d}",
                "region": choice([l[0] for l in sensor_locations]),
                "start_time": (datetime.now() - timedelta(days=randint(0, 30))).isoformat(),
                "status": choice(["active", "completed", "scheduled"]),
                "robots": {
                    "ocean_drones": randint(2, 10),
                    "surface_vessels": randint(1, 5),
                    "underwater_units": randint(1, 5)
                },
                "waste_collected": randint(500, 5000),
                "next_deployment": choice([l[0] for l in sensor_locations])
            })
        self.cleanup_logs.delete_many({})
        self.cleanup_logs.insert_many(missions)
        print(f"Seeded {len(missions)} cleanup missions.")
        # --- Citizen Reports ---
        reports = []
        for i in range(60):
            loc = choice(sensor_locations)
            reports.append({
                "report_id": f"CR-{i:04d}",
                "timestamp": (datetime.now() - timedelta(hours=randint(0, 200))).isoformat(),
                "location": {"type": "Point", "coordinates": [loc[2], loc[1]]},
                "location_name": loc[0],
                "severity": choice(["low", "medium", "high"]),
                "status": choice(["pending", "investigating", "resolved"]),
                "reporter_type": choice(["citizen", "tourist", "volunteer", "student"]),
                "pollution_type": choice(["plastic_bottles", "plastic_bags", "fishing_gear", "microplastics", "mixed_waste"])
            })
        self.pollution_reports.delete_many({})
        self.pollution_reports.insert_many(reports)
        print(f"Seeded {len(reports)} citizen reports.")
        # --- Campaigns ---
        campaigns = []
        for i in range(10):
            campaigns.append({
                "campaign_id": f"CAMP-{i:03d}",
                "title": choice(["Awareness", "Cleanup", "Reporting", "Education"]),
                "description": "Auto-seeded campaign.",
                "status": "active",
                "participants": randint(100, 10000),
                "duration": f"{randint(7, 30)} days",
                "created_at": (datetime.now() - timedelta(days=randint(0, 60))).isoformat()
            })
        self.campaigns.delete_many({})
        self.campaigns.insert_many(campaigns)
        print(f"Seeded {len(campaigns)} campaigns.")

    def get_cleanup_data(self):
        """Aggregate cleanup mission data for dashboard/API."""
        try:
            robots = {'ocean_drones': 0, 'surface_vessels': 0, 'underwater_units': 0}
            waste_collected_today = 0
            hotspots_addressed = 0
            active_missions = 0
            next_deployment = None
            missions = list(self.cleanup_logs.find())
            for mission in missions:
                r = mission.get('robots', {})
                robots['ocean_drones'] += r.get('ocean_drones', 0)
                robots['surface_vessels'] += r.get('surface_vessels', 0)
                robots['underwater_units'] += r.get('underwater_units', 0)
                if mission.get('status') == 'active':
                    active_missions += 1
                waste_collected_today += mission.get('waste_collected', 0)
                if mission.get('status') == 'completed':
                    hotspots_addressed += 1
                if not next_deployment and mission.get('next_deployment'):
                    next_deployment = mission['next_deployment']
            return {
                'active_missions': active_missions,
                'cleanup_robots': robots,
                'waste_collected_today': waste_collected_today,
                'hotspots_addressed': hotspots_addressed,
                'next_deployment': next_deployment or ''
            }
        except Exception as e:
            print(f"Error aggregating cleanup data: {e}")
            return {
                'active_missions': 0,
                'cleanup_robots': {'ocean_drones': 0, 'surface_vessels': 0, 'underwater_units': 0},
                'waste_collected_today': 0,
                'hotspots_addressed': 0,
                'next_deployment': ''
            }

# Initialize MongoDB manager
mongodb = MongoDBManager()

# Auto-seed DB if empty
if mongodb.sensors.count_documents({}) == 0:
    print("Seeding MongoDB with initial data...")
    mongodb.seed_db()
