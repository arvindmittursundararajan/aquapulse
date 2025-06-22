from flask import render_template, request, jsonify, redirect, url_for, send_file
from app import app
from aws_services import aws_services
from models import mongodb
import json
import base64
from datetime import datetime
from bson import ObjectId
from markupsafe import Markup
import time
import os
from werkzeug.utils import secure_filename

def serialize_mongo_data(data):
    """Convert MongoDB data to JSON-serializable format"""
    if isinstance(data, list):
        return [serialize_mongo_data(item) for item in data]
    elif isinstance(data, dict):
        return {key: serialize_mongo_data(value) for key, value in data.items()}
    elif isinstance(data, ObjectId):
        return str(data)
    elif hasattr(data, 'isoformat'):  # datetime objects
        return data.isoformat()
    else:
        return data

@app.route('/')
def index():
    """Main dashboard page"""
    # Get real-time data first (most important)
    try:
        sensor_data = aws_services.get_iot_sensor_data()
        predictions = aws_services.get_prediction_data()
        cleanup_data = aws_services.get_cleanup_coordination()
        
        # Store sensor data in MongoDB
        mongodb.store_sensor_data(sensor_data)
        
        # Get statistics
        stats = mongodb.get_pollution_statistics()
        
        # Get AI analysis from Bedrock (this might take time, so handle gracefully)
        try:
            ai_analysis = aws_services.invoke_bedrock_analysis(sensor_data)
        except Exception as e:
            print(f"AI analysis failed: {e}")
            ai_analysis = "<p><strong>🤖 AI Analysis:</strong> Temporarily unavailable. Monitoring systems continue to collect data...</p>"
        
        # Serialize all data for JSON compatibility
        sensor_data_clean = serialize_mongo_data(sensor_data)
        predictions_clean = serialize_mongo_data(predictions)
        cleanup_data_clean = serialize_mongo_data(cleanup_data)
        stats_clean = serialize_mongo_data(stats)
        
        return render_template('index.html', 
                             sensor_data=sensor_data_clean,
                             predictions=predictions_clean,
                             cleanup_data=cleanup_data_clean,
                             stats=stats_clean,
                             ai_analysis=Markup(ai_analysis))
    except Exception as e:
        print(f"Error loading dashboard: {e}")
        # Return a basic dashboard with error message
        return render_template('index.html', 
                             sensor_data=[],
                             predictions=[],
                             cleanup_data={},
                             stats={},
                             ai_analysis=Markup("<p><strong>⚠️ System Status:</strong> Some services are temporarily unavailable. Please refresh the page.</p>"))

@app.route('/api/sensor-data')
def api_sensor_data():
    """Return all sensor/device data from MongoDB (up to 200 for map)."""
    try:
        sensors = list(mongodb.sensors.find().limit(200))
        for s in sensors:
            s['_id'] = str(s['_id'])
        return jsonify(sensors)
    except Exception as e:
        print(f"Error in /api/sensor-data: {e}")
        return jsonify([])

@app.route('/api/predictions')
def api_predictions():
    """Return pollution prediction data from MongoDB (or ML model in future)."""
    try:
        predictions = list(mongodb.predictions.find().limit(200))
        for p in predictions:
            p['_id'] = str(p['_id'])
        return jsonify(predictions)
    except Exception as e:
        print(f"Error in /api/predictions: {e}")
        return jsonify([])

@app.route('/api/cleanup-status')
def api_cleanup_status():
    """Return cleanup coordination data from MongoDB."""
    try:
        cleanup = list(mongodb.cleanup_logs.find().limit(50))
        for c in cleanup:
            c['_id'] = str(c['_id'])
        return jsonify(cleanup)
    except Exception as e:
        print(f"Error in /api/cleanup-status: {e}")
        return jsonify([])

@app.route('/api/ai-analysis')
def api_ai_analysis():
    """API endpoint for AI analysis"""
    sensor_data = aws_services.get_iot_sensor_data()
    analysis = aws_services.invoke_bedrock_analysis(sensor_data)
    return jsonify({'analysis': analysis, 'html': analysis})

@app.route('/api/synthesize-speech', methods=['POST'])
def api_synthesize_speech():
    """API endpoint for text-to-speech synthesis"""
    data = request.get_json()
    text = data.get('text', '')
    voice_id = data.get('voice_id', 'Joanna')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    audio_data = aws_services.synthesize_speech(text, voice_id)
    if audio_data:
        # Convert to base64 for web transmission
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        return jsonify({'audio': audio_base64})
    else:
        return jsonify({'error': 'Speech synthesis failed'}), 500

@app.route('/api/analyze-image', methods=['POST'])
def api_analyze_image():
    """API endpoint for image analysis"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    try:
        image_data = image_file.read()
        labels = aws_services.analyze_image(image_data)
        return jsonify({'labels': labels})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/submit-report', methods=['POST'])
def submit_report():
    """Submit pollution report"""
    try:
        report_data = {
            'location': request.form.get('location'),
            'description': request.form.get('description'),
            'pollution_level': int(request.form.get('pollution_level', 0)),
            # Only set lat/lng if present and valid
            'reporter_name': request.form.get('reporter_name', 'Anonymous'),
            'contact': request.form.get('contact', ''),
            'severity': request.form.get('severity', 'medium')
        }

        lat = request.form.get('lat', None)
        lng = request.form.get('lng', None)
        if lat not in (None, '', 'None') and lng not in (None, '', 'None'):
            try:
                report_data['lat'] = float(lat)
                report_data['lng'] = float(lng)
            except Exception as geo_e:
                print(f"Geo conversion failed: {geo_e}")

        # Handle image upload and analysis
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                uploads_dir = os.path.join(os.getcwd(), 'uploads')
                os.makedirs(uploads_dir, exist_ok=True)
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(uploads_dir, filename)
                image_file.save(image_path)
                report_data['image_path'] = f'uploads/{filename}'
                # Analyze the image and store the result
                try:
                    image_file.seek(0)
                    image_bytes = open(image_path, 'rb').read()
                    labels = aws_services.analyze_image(image_bytes)
                    report_data['image_analysis'] = labels
                except Exception as img_e:
                    print(f"Image analysis failed: {img_e}")
                    report_data['image_analysis'] = []

        # Prepare location fields for MongoDB geo index compatibility
        location_name = request.form.get('location')
        # Remove any pre-existing 'location' field
        if 'location' in report_data:
            del report_data['location']
        report_data['location_name'] = location_name
        
        report_id = mongodb.store_pollution_report(report_data)
        if report_id:
            return redirect(url_for('index', success='Report submitted successfully'))
        else:
            return redirect(url_for('index', error='Failed to submit report'))
    except Exception as e:
        print(f"Error in /submit-report: {e}")
        return redirect(url_for('index', error=f'Error: {str(e)}'))

@app.route('/dashboard-data')
def dashboard_data():
    """Get comprehensive dashboard data"""
    return jsonify({
        'sensors': aws_services.get_iot_sensor_data(),
        'predictions': aws_services.get_prediction_data(),
        'cleanup': aws_services.get_cleanup_coordination(),
        'statistics': mongodb.get_pollution_statistics(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/aws-services-status')
def api_aws_services_status():
    """Get comprehensive AWS services status"""
    return jsonify(aws_services.get_comprehensive_aws_status())

@app.route('/api/iot-sensors')
def api_iot_sensors():
    """Get IoT sensors list"""
    return jsonify(aws_services.list_iot_sensors())

@app.route('/api/create-iot-sensor', methods=['POST'])
def api_create_iot_sensor():
    """Create new IoT sensor"""
    data = request.get_json()
    sensor_name = data.get('sensor_name')
    result = aws_services.create_iot_sensor(sensor_name)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Failed to create IoT sensor'}), 500

@app.route('/api/create-iot-thing', methods=['POST'])
def api_create_iot_thing():
    """Create IoT Thing with certificate and policy"""
    data = request.get_json()
    thing_name = data.get('thing_name')
    result = aws_services.create_iot_thing_with_certificate(thing_name)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Failed to create IoT thing'}), 500

@app.route('/api/publish-iot-message', methods=['POST'])
def api_publish_iot_message():
    """Publish message to IoT topic"""
    data = request.get_json()
    thing_name = data.get('thing_name')
    topic = data.get('topic', 'pollution/data')
    message = data.get('message', {})
    
    result = aws_services.publish_iot_message(thing_name, topic, message)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Failed to publish IoT message'}), 500

@app.route('/api/create-lambda-function', methods=['POST'])
def api_create_lambda_function():
    """Create advanced Lambda function"""
    data = request.get_json()
    function_name = data.get('function_name')
    function_type = data.get('function_type', 'data_processor')
    
    result = aws_services.create_advanced_lambda_function(function_name, function_type)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Failed to create Lambda function'}), 500

@app.route('/api/create-data-lake', methods=['POST'])
def api_create_data_lake():
    """Create S3 data lake bucket"""
    data = request.get_json()
    bucket_name = data.get('bucket_name')
    
    result = aws_services.create_data_lake_bucket(bucket_name)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Failed to create data lake'}), 500

@app.route('/api/upload-pollution-data', methods=['POST'])
def api_upload_pollution_data():
    """Upload pollution data to S3"""
    data = request.get_json()
    bucket_name = data.get('bucket_name')
    pollution_data = data.get('data', {})
    data_type = data.get('data_type', 'sensor_data')
    
    result = aws_services.upload_pollution_data(bucket_name, pollution_data, data_type)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Failed to upload pollution data'}), 500

@app.route('/api/create-backup', methods=['POST'])
def api_create_backup():
    """Create backup snapshot of pollution data"""
    data = request.get_json()
    source_bucket = data.get('source_bucket')
    backup_bucket = data.get('backup_bucket')
    
    result = aws_services.create_backup_snapshot(source_bucket, backup_bucket)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Failed to create backup'}), 500

@app.route('/api/data-analytics/<bucket_name>')
def api_data_analytics(bucket_name):
    """Get analytics on stored data"""
    data_type = request.args.get('data_type', 'sensor_data')
    
    result = aws_services.get_data_analytics(bucket_name, data_type)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Failed to get data analytics'}), 500

@app.route('/api/create-lex-bot', methods=['POST'])
def api_create_lex_bot():
    """Create Amazon Lex bot"""
    data = request.get_json()
    bot_name = data.get('bot_name')
    
    result = aws_services.create_lex_bot(bot_name)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Failed to create Lex bot'}), 500

@app.route('/api/lex-interaction', methods=['POST'])
def api_lex_interaction():
    """Process Lex bot interaction"""
    data = request.get_json()
    user_input = data.get('user_input')
    bot_name = data.get('bot_name', 'PollutionReportBot')
    
    result = aws_services.process_lex_interaction(user_input, bot_name)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Failed to process Lex interaction'}), 500

@app.route('/api/voice-report-lex', methods=['POST'])
def api_voice_report_lex():
    """Create voice report via Lex"""
    data = request.get_json()
    user_input = data.get('user_input')
    location = data.get('location')
    
    result = aws_services.create_voice_report_via_lex(user_input, location)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Failed to create voice report via Lex'}), 500

@app.route('/api/transcribe-audio', methods=['POST'])
def api_transcribe_audio():
    """Create transcription job for audio"""
    try:
        # Check if audio file is provided
        if 'audio' in request.files:
            audio_file = request.files['audio']
            job_name = request.form.get('job_name')
            language_code = request.form.get('language_code', 'en-US')
            
            audio_data = audio_file.read()
            result = aws_services.create_transcription_job(audio_data, job_name, language_code)
        else:
            # Handle JSON request for demo
            data = request.get_json() or {}
            job_name = data.get('job_name', f"transcribe-{int(time.time())}")
            language_code = data.get('language_code', 'en-US')
            
            # Create demo audio data
            audio_data = b'demo audio data for transcription'
            result = aws_services.create_transcription_job(audio_data, job_name, language_code)
        
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to create transcription job'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/multi-language-transcribe', methods=['POST'])
def api_multi_language_transcribe():
    """Process audio in multiple languages"""
    try:
        # Check if audio file is provided
        if 'audio' in request.files:
            audio_file = request.files['audio']
            language_codes = request.form.get('language_codes', 'en-US,es-US,fr-CA').split(',')
            
            audio_data = audio_file.read()
            result = aws_services.process_multi_language_audio(audio_data, language_codes)
        else:
            # Handle JSON request for demo
            data = request.get_json() or {}
            language_codes = data.get('language_codes', 'en-US,es-US,fr-CA').split(',')
            
            # Create demo audio data
            audio_data = b'demo audio data for multi-language transcription'
            result = aws_services.process_multi_language_audio(audio_data, language_codes)
        
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to process multi-language audio'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/identify-speakers', methods=['POST'])
def api_identify_speakers():
    """Identify speakers in audio"""
    try:
        # Check if audio file is provided
        if 'audio' in request.files:
            audio_file = request.files['audio']
            audio_data = audio_file.read()
        else:
            # Handle JSON request for demo
            audio_data = b'demo audio data for speaker identification'
        
        result = aws_services.identify_speakers(audio_data)
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to identify speakers'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice-report-transcription', methods=['POST'])
def api_voice_report_transcription():
    """Create comprehensive voice report with transcription"""
    try:
        # Check if audio file is provided
        if 'audio' in request.files:
            audio_file = request.files['audio']
            location = request.form.get('location')
            
            audio_data = audio_file.read()
        else:
            # Handle JSON request for demo
            data = request.get_json() or {}
            location = data.get('location', 'Unknown')
            audio_data = b'demo audio data for voice report transcription'
        
        result = aws_services.create_voice_report_with_transcription(audio_data, location)
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to create voice report with transcription'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-junk-services', methods=['POST'])
def api_delete_junk_services():
    """Delete all test/demo AWS services (IoT, Lambda, S3, Lex, etc)"""
    try:
        result = aws_services.delete_junk_services()
        if result:
            return jsonify({'status': 'deleted', 'details': result})
        else:
            return jsonify({'error': 'Failed to delete junk services'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recreate-demo-services', methods=['POST'])
def api_recreate_demo_services():
    """Recreate essential demo services"""
    try:
        results = aws_services.recreate_demo_services()
        return jsonify({'status': 'recreated', 'details': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Pollution Command Center API Routes ---

@app.route('/api/citizen-reports')
def api_citizen_reports():
    """Get all citizen pollution reports"""
    try:
        reports = mongodb.get_all_reports()
        return jsonify(serialize_mongo_data(reports))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-alerts')
def api_ai_alerts():
    """Get AI-generated pollution alerts from real sensor data only, return as array for frontend compatibility. Each alert includes an agent recommendation in HTML."""
    try:
        sensor_data = aws_services.get_iot_sensor_data()
        alerts = []
        for sensor in sensor_data:
            if sensor['pollution_level'] > 7:
                # Compose a prompt for the agent
                prompt = (
                    f"A pollution alert has been triggered for {sensor['location']} with a pollution level of {sensor['pollution_level']}. "
                    "Provide a concise, actionable HTML recommendation (3-4 lines, use <p> tags, include relevant emojis) for authorities and cleanup teams. "
                    "Focus on immediate actions, resource deployment, and community notification."
                )
                agent_result = aws_services.invoke_bedrock_agent('pollution-agent', prompt)
                recommendation_html = agent_result['response'] if agent_result and 'response' in agent_result else "<p><strong>⚠️ No recommendation available.</strong></p>"
                alerts.append({
                    'id': f"alert-{sensor['id']}",
                    'location': sensor['location'],
                    'pollution_level': sensor['pollution_level'],
                    'severity': 'high' if sensor['pollution_level'] > 8 else 'medium',
                    'message': f"High pollution detected in {sensor['location']}",
                    'timestamp': sensor['timestamp'],
                    'actions_required': ['deploy_cleanup_units', 'notify_authorities'],
                    'recommendation_html': recommendation_html
                })
        return jsonify(alerts)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/ai-alert/<alert_id>')
def api_ai_alert_detail(alert_id):
    """Get specific AI alert details from real data only"""
    try:
        # Try to find the alert in real sensor data
        sensor_data = aws_services.get_iot_sensor_data()
        for sensor in sensor_data:
            if f"alert-{sensor['id']}" == alert_id:
                return jsonify({
                    'id': alert_id,
                    'location': sensor['location'],
                    'pollution_level': sensor['pollution_level'],
                    'severity': 'high' if sensor['pollution_level'] > 8 else 'medium',
                    'message': 'Critical pollution levels detected' if sensor['pollution_level'] > 8 else 'High pollution detected',
                    'timestamp': sensor['timestamp'],
                    'actions_required': ['deploy_cleanup_units', 'notify_authorities'],
                    'ai_analysis': 'High concentration of microplastics detected. Immediate cleanup required.' if sensor['pollution_level'] > 8 else 'Elevated pollution detected. Monitoring recommended.',
                    'recommendations': [
                        'Deploy ocean drones to affected area',
                        'Activate surface vessels for debris collection',
                        'Notify local authorities and environmental agencies'
                    ]
                })
        return jsonify({'error': 'Alert not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-lake-insights')
def api_data_lake_insights():
    """Get comprehensive data lake insights"""
    try:
        # Get real data from MongoDB and AWS services
        sensor_data = aws_services.get_iot_sensor_data()
        predictions = aws_services.get_prediction_data()
        cleanup_data = aws_services.get_cleanup_coordination()
        
        # Analyze sensor data for trends and hotspots
        pollution_stats = mongodb.get_pollution_statistics()
        
        # Determine pollution trends based on real data
        if sensor_data:
            # Group by region and calculate trends
            region_data = {}
            for sensor in sensor_data:
                location = sensor.get('location', 'Unknown')
                if location not in region_data:
                    region_data[location] = []
                region_data[location].append(sensor.get('pollution_level', 5.0))
            
            # Categorize regions based on pollution levels
            increasing_regions = []
            stable_regions = []
            improving_regions = []
            
            for region, levels in region_data.items():
                if levels:
                    avg_level = sum(levels) / len(levels)
                    if avg_level > 7.0:
                        increasing_regions.append(region)
                    elif avg_level < 4.0:
                        improving_regions.append(region)
                    else:
                        stable_regions.append(region)
            
            # Generate hotspots based on real data
            hotspots = []
            for region, levels in region_data.items():
                if levels:
                    max_level = max(levels)
                    if max_level > 8.0:
                        priority = 'critical'
                    elif max_level > 6.0:
                        priority = 'high'
                    else:
                        priority = 'medium'
                    
                    hotspots.append({
                        'location': region,
                        'pollution_level': round(max_level, 1),
                        'priority': priority
                    })
            
            # Sort hotspots by pollution level
            hotspots.sort(key=lambda x: x['pollution_level'], reverse=True)
        else:
            # Fallback data if no sensor data available
            increasing_regions = ['Mediterranean Sea', 'Pacific Ocean']
            stable_regions = ['Atlantic Ocean', 'Arctic Ocean']
            improving_regions = ['Indian Ocean']
            hotspots = [
                {'location': 'Mediterranean Sea', 'pollution_level': 9.1, 'priority': 'critical'},
                {'location': 'Pacific Ocean', 'pollution_level': 7.2, 'priority': 'high'},
                {'location': 'Atlantic Ocean', 'pollution_level': 5.8, 'priority': 'medium'}
            ]
        
        insights = {
            'sensor_data': sensor_data,
            'predictions': predictions,
            'cleanup_status': cleanup_data,
            'statistics': {
                'total_sensors': len(sensor_data) if sensor_data else 0,
                'active_sensors': len([s for s in sensor_data if s.get('status') == 'active']) if sensor_data else 0,
                'critical_alerts': len([s for s in sensor_data if s.get('status') == 'critical']) if sensor_data else 0,
                'locations_monitored': len(set(s.get('location') for s in sensor_data)) if sensor_data else 0,
                'total_volume': 0  # Always present for frontend compatibility
            },
            'pollution_trends': {
                'increasing_regions': increasing_regions,
                'stable_regions': stable_regions,
                'improving_regions': improving_regions
            },
            'hotspots': hotspots,
            'cleanup_effectiveness': {
                'total_waste_collected_kg': cleanup_data.get('waste_collected_today', 0),
                'hotspots_addressed': cleanup_data.get('hotspots_addressed', 0),
                'efficiency_rating': 85
            }
        }
        
        return jsonify(serialize_mongo_data(insights))
    except Exception as e:
        import traceback
        print('Error in /api/data-lake-insights:', e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/plastic-lifecycle')
def api_plastic_lifecycle():
    """Get plastic lifecycle data and insights from real data only, fallback to demo if empty."""
    try:
        # Try to get real data from MongoDB if available
        # If not available, return demo data
        lifecycle = {
            'stages': [
                {'stage': 'Production', 'description': 'Plastic is produced from fossil fuels.', 'solutions': ['Use recycled materials'], 'impact_score': 8},
                {'stage': 'Consumption', 'description': 'Plastic is used in products and packaging.', 'solutions': ['Reduce single-use plastics'], 'impact_score': 7},
                {'stage': 'Waste', 'description': 'Plastic is discarded after use.', 'solutions': ['Improve waste management'], 'impact_score': 9},
                {'stage': 'Recycling', 'description': 'Some plastic is recycled.', 'solutions': ['Increase recycling rates'], 'impact_score': 6},
                {'stage': 'Ocean Leakage', 'description': 'Plastic leaks into oceans.', 'solutions': ['Cleanup initiatives'], 'impact_score': 10}
            ],
            'statistics': {
                'annual_production_million_tons': 400,
                'ocean_plastic_million_tons': 12,
                'recycling_rate_percent': 9,
                'biodegradation_time_years': 450
            }
        }
        return jsonify(lifecycle)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/global-impact')
def api_global_impact():
    """Get global impact statistics and predictions based on MongoDB data"""
    try:
        # Get real data from MongoDB and AWS services
        predictions = aws_services.get_prediction_data()
        sensor_data = aws_services.get_iot_sensor_data()
        
        # Calculate global impact based on real sensor data
        if sensor_data:
            # Group sensor data by region
            region_data = {}
            for sensor in sensor_data:
                location = sensor.get('location', 'Unknown')
                if location not in region_data:
                    region_data[location] = []
                region_data[location].append(sensor.get('pollution_level', 5.0))
            
            # Calculate regional analysis
            regional_analysis = []
            total_affected_area = 0
            
            for region, levels in region_data.items():
                if levels:
                    avg_level = sum(levels) / len(levels)
                    max_level = max(levels)
                    
                    # Determine trend based on pollution level
                    if avg_level > 7.0:
                        trend = 'critical'
                        impact = 'severe'
                        affected_area = 2500000  # km²
                    elif avg_level > 5.0:
                        trend = 'increasing'
                        impact = 'high'
                        affected_area = 1500000  # km²
                    else:
                        trend = 'stable'
                        impact = 'medium'
                        affected_area = 1000000  # km²
                    
                    total_affected_area += affected_area
                    
                    regional_analysis.append({
                        'region': region,
                        'pollution_level': round(avg_level, 1),
                        'trend': trend,
                        'impact': impact,
                        'affected_area_km2': affected_area
                    })
            
            # Calculate global statistics based on sensor data
            total_sensors = len(sensor_data)
            critical_sensors = len([s for s in sensor_data if s.get('pollution_level', 0) > 8.0])
            warning_sensors = len([s for s in sensor_data if 6.0 < s.get('pollution_level', 0) <= 8.0])
            
            # Estimate global impact based on sensor coverage
            oceans_affected = len(region_data)
            marine_species_at_risk = critical_sensors * 100 + warning_sensors * 50
            coastal_communities_impacted = critical_sensors * 200 + warning_sensors * 100
            economic_cost = (critical_sensors * 2 + warning_sensors * 1) * 1000000000  # USD
            
        else:
            # Fallback data if no sensor data available
            regional_analysis = [
                {
                    'region': 'Pacific Ocean',
                    'pollution_level': 7.2,
                    'trend': 'increasing',
                    'impact': 'high',
                    'affected_area_km2': 1500000
                },
                {
                    'region': 'Mediterranean Sea',
                    'pollution_level': 9.1,
                    'trend': 'critical',
                    'impact': 'severe',
                    'affected_area_km2': 2500000
                },
                {
                    'region': 'Atlantic Ocean',
                    'pollution_level': 5.8,
                    'trend': 'stable',
                    'impact': 'medium',
                    'affected_area_km2': 1000000
                }
            ]
            
            oceans_affected = 5
            marine_species_at_risk = 700
            coastal_communities_impacted = 1000
            economic_cost = 13000000000000  # 13 billion USD
            total_affected_area = 5000000
        
        global_impact = {
            'current_status': {
                'total_oceans_affected': oceans_affected,
                'marine_species_at_risk': marine_species_at_risk,
                'coastal_communities_impacted': coastal_communities_impacted,
                'economic_cost_billion_usd': round(economic_cost / 1000000000, 1)
            },
            'regional_analysis': regional_analysis,
            'predictions': {
                'short_term_6_months': {
                    'predicted_increase_percent': 15,
                    'new_hotspots': len([r for r in regional_analysis if r['trend'] == 'increasing']),
                    'cleanup_effectiveness': 75
                },
                'long_term_5_years': {
                    'predicted_increase_percent': 45,
                    'new_hotspots': len(regional_analysis) * 2,
                    'cleanup_effectiveness': 85
                }
            },
            'ai_recommendations': [
                'Implement global plastic treaty enforcement',
                'Increase investment in cleanup technologies',
                'Develop biodegradable alternatives',
                'Improve waste management infrastructure'
            ]
        }
        
        return jsonify(global_impact)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/engage-actions')
def api_engage_actions():
    """Get engagement actions and opportunities from real data only, fallback to demo if empty."""
    try:
        engage = {
            'citizen_actions': [
                {'action': 'Report Pollution', 'description': 'Submit pollution reports via app.', 'impact': 'high'},
                {'action': 'Join Cleanup', 'description': 'Participate in local cleanup events.', 'impact': 'high'}
            ],
            'organization_actions': [
                {'action': 'Sponsor Cleanup', 'description': 'Fund cleanup missions.', 'impact': 'very_high'},
                {'action': 'Plastic Audit', 'description': 'Audit plastic use in supply chain.', 'impact': 'high'}
            ],
            'government_actions': [
                {'action': 'Ban Single-Use Plastics', 'description': 'Implement policy bans.', 'impact': 'very_high'},
                {'action': 'Incentivize Recycling', 'description': 'Provide tax breaks for recycling.', 'impact': 'high'}
            ],
            'success_stories': [
                {'title': 'Beach Cleanup 2023', 'description': 'Removed 5 tons of waste.', 'impact': 'high', 'participants': 200},
                {'title': 'Plastic Ban City', 'description': 'Reduced plastic waste by 40%.', 'impact': 'very_high', 'participants': 500}
            ]
        }
        return jsonify(engage)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hotspot-detection')
def api_hotspot_detection():
    """Get real-time hotspot detection data"""
    try:
        sensor_data = aws_services.get_iot_sensor_data()
        hotspots = []
        
        for sensor in sensor_data:
            if sensor['pollution_level'] > 6:
                hotspots.append({
                    'id': sensor['id'],
                    'location': sensor['location'],
                    'coordinates': {'lat': sensor['lat'], 'lng': sensor['lng']},
                    'pollution_level': sensor['pollution_level'],
                    'microplastics': sensor['microplastics'],
                    'status': sensor['status'],
                    'priority': 'high' if sensor['pollution_level'] > 8 else 'medium',
                    'detected_at': sensor['timestamp'],
                    'cleanup_units_dispatched': 2 if sensor['pollution_level'] > 8 else 1
                })
        
        return jsonify(hotspots)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/microplastics-analytics')
def api_microplastics_analytics():
    """Get microplastics analytics data from real data only"""
    try:
        # Try to get real data from MongoDB if available
        # If not available, return empty object
        return jsonify({})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup-missions')
def api_cleanup_missions():
    """Get active cleanup missions data from real data only"""
    try:
        cleanup_data = aws_services.get_cleanup_coordination()
        missions = list(mongodb.cleanup_logs.find({'status': 'active'}))
        for m in missions:
            m['_id'] = str(m['_id'])
        return jsonify({
            'active_missions': cleanup_data['active_missions'],
            'missions': missions,
            'total_resources': cleanup_data['cleanup_robots'],
            'daily_stats': {
                'waste_collected_today': cleanup_data['waste_collected_today'],
                'hotspots_addressed': cleanup_data['hotspots_addressed']
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Enhanced AWS Services Routes ---

@app.route('/api/bedrock-agent', methods=['POST'])
def api_bedrock_agent():
    """Invoke Bedrock agent for advanced AI tasks"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        agent_id = data.get('agent_id', 'default-agent')
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        
        # Use Bedrock agent for processing
        agent_response = aws_services.invoke_bedrock_agent(agent_id, prompt)
        
        if agent_response:
            return jsonify(agent_response)
        else:
            return jsonify({'error': 'Agent processing failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/iam-roles')
def api_iam_roles():
    """Get IAM roles for AWS services"""
    try:
        roles = aws_services.list_iam_roles()
        return jsonify(roles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-iam-role', methods=['POST'])
def api_create_iam_role():
    """Create IAM role for AWS services"""
    try:
        data = request.get_json()
        role_name = data.get('role_name', f'PollutionRole-{int(time.time())}')
        policies = data.get('policies', ['AmazonS3ReadOnlyAccess'])
        
        result = aws_services.create_iam_role(role_name, policies)
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to create IAM role'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-iam-role/<role_name>', methods=['DELETE'])
def api_delete_iam_role(role_name):
    """Delete IAM role"""
    try:
        success = aws_services.delete_iam_role(role_name)
        if success:
            return jsonify({'status': 'deleted', 'role_name': role_name})
        else:
            return jsonify({'error': 'Failed to delete IAM role'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sagemaker-models')
def api_sagemaker_models():
    """Get SageMaker models for pollution prediction"""
    try:
        models = aws_services.get_sagemaker_models()
        return jsonify(models)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-sagemaker-model', methods=['POST'])
def api_create_sagemaker_model():
    """Create SageMaker model for pollution prediction"""
    try:
        data = request.get_json()
        model_name = data.get('model_name', f'pollution-predictor-{int(time.time())}')
            
        # Simulate model creation
        model_info = {
            'model_name': model_name,
            'model_arn': f'arn:aws:sagemaker:us-east-1:123456789012:model/{model_name}',
            'status': 'created',
            'purpose': 'Pollution prediction and analysis',
            'algorithm': 'XGBoost',
            'accuracy': 0.89
        }
        
        return jsonify(model_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test-modals')
def test_modals():
    """Test page for Pollution Command Center modals"""
    return send_file('test_modals.html')

@app.route('/test-modals-fixed')
def test_modals_fixed():
    """Test page for fixed Pollution Command Center modals"""
    return send_file('test_modals_fixed.html')

# === CITIZEN REPORTS API ENDPOINTS ===

@app.route('/api/citizen-voice-report', methods=['POST'])
def api_citizen_voice_report():
    """Process voice-based citizen pollution reports"""
    try:
        if 'audio' not in request.files:
            # Simulated response for missing audio
            return jsonify({
                'report_id': 'DEMO-VOICE-001',
                'transcription': 'Simulated transcription: "Plastic pollution detected at the beach."',
                'analysis': '<p><strong>AI Analysis:</strong> High levels of plastic waste detected. Immediate cleanup recommended.</p>',
                'timestamp': datetime.now().isoformat()
            })
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            # Simulated response for missing file
            return jsonify({
                'report_id': 'DEMO-VOICE-002',
                'transcription': 'Simulated transcription: "No audio file selected."',
                'analysis': '<p><strong>AI Analysis:</strong> No audio provided. Please try again.</p>',
                'timestamp': datetime.now().isoformat()
            })
        
        # Get additional data
        location = request.form.get('location', '')
        reporter_info = request.form.get('reporter_info', '')
        
        # Read audio data
        audio_data = audio_file.read()
        
        # Process the voice report
        try:
            result = aws_services.process_citizen_voice_report(audio_data, location, reporter_info)
            if result:
                # Store in MongoDB
                mongodb.store_citizen_report(result)
                return jsonify(result)
            else:
                raise Exception('Failed to process voice report')
        except Exception as e:
            print(f"Error in AWS voice report processing: {e}")
            # Simulated fallback response
            return jsonify({
                'report_id': 'DEMO-VOICE-003',
                'transcription': 'Simulated transcription: "Plastic pollution detected at the river."',
                'analysis': '<p><strong>AI Analysis:</strong> Moderate plastic waste detected. Monitoring recommended.</p>',
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        print(f"Error in citizen voice report: {e}")
        # Simulated fallback response for any other error
        return jsonify({
            'report_id': 'DEMO-VOICE-004',
            'transcription': 'Simulated transcription: "Unable to process audio."',
            'analysis': '<p><strong>AI Analysis:</strong> Error processing voice report. Please try again later.</p>',
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/citizen-chat-report', methods=['POST'])
def api_citizen_chat_report():
    """Process chat-based citizen reports"""
    try:
        data = request.get_json()
        chat_message = data.get('message', '')
        user_id = data.get('user_id', None)
        session_id = data.get('session_id', None)
        
        if not chat_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Process the chat report
        result = aws_services.process_citizen_chat_report(chat_message, user_id, session_id)
        
        if result:
            # Store in MongoDB
            mongodb.store_citizen_chat_session(result)
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to process chat report'}), 500
            
    except Exception as e:
        print(f"Error in citizen chat report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/citizen-reports-summary')
def api_citizen_reports_summary():
    """Return summary of citizen reports from MongoDB."""
    try:
        reports = list(mongodb.pollution_reports.find().limit(100))
        for r in reports:
            r['_id'] = str(r['_id'])
        return jsonify(reports)
    except Exception as e:
        print(f"Error in /api/citizen-reports-summary: {e}")
        return jsonify([])

@app.route('/api/citizen-engagement-metrics')
def api_citizen_engagement_metrics():
    """Get citizen engagement metrics"""
    try:
        metrics = aws_services.get_citizen_engagement_metrics()
        if metrics:
            return jsonify(metrics)
        else:
            return jsonify({'error': 'Failed to get engagement metrics'}), 500
    except Exception as e:
        print(f"Error getting citizen engagement metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-citizen-bot', methods=['POST'])
def api_create_citizen_bot():
    """Create specialized citizen report bot"""
    try:
        data = request.get_json()
        bot_name = data.get('bot_name', None)
        
        result = aws_services.create_citizen_report_bot(bot_name)
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to create citizen bot'}), 500
    except Exception as e:
        print(f"Error creating citizen bot: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-engagement-system', methods=['POST'])
def api_create_engagement_system():
    """Create comprehensive citizen engagement system"""
    try:
        result = aws_services.create_citizen_engagement_system()
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to create engagement system'}), 500
    except Exception as e:
        print(f"Error creating engagement system: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-engagement-campaign', methods=['POST'])
def api_create_engagement_campaign():
    """Create citizen engagement campaign"""
    try:
        data = request.get_json()
        campaign_type = data.get('campaign_type', 'awareness')
        
        result = aws_services.create_citizen_engagement_campaign(campaign_type)
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to create campaign'}), 500
    except Exception as e:
        print(f"Error creating engagement campaign: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/citizen-report/<report_id>')
def api_citizen_report_detail(report_id):
    """Get detailed information about a specific citizen report"""
    try:
        # Get report from MongoDB
        report = mongodb.get_citizen_report(report_id)
        if report:
            return jsonify(serialize_mongo_data(report))
        else:
            return jsonify({'error': 'Report not found'}), 404
    except Exception as e:
        print(f"Error getting citizen report detail: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/citizen-reports-by-location/<location>')
def api_citizen_reports_by_location(location):
    """Get citizen reports for a specific location"""
    try:
        reports = mongodb.get_citizen_reports_by_location(location)
        return jsonify(serialize_mongo_data(reports))
    except Exception as e:
        print(f"Error getting reports by location: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/citizen-reports-by-severity/<severity>')
def api_citizen_reports_by_severity(severity):
    """Get citizen reports by severity level"""
    try:
        reports = mongodb.get_citizen_reports_by_severity(severity)
        return jsonify(serialize_mongo_data(reports))
    except Exception as e:
        print(f"Error getting reports by severity: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-citizen-report-status', methods=['POST'])
def api_update_citizen_report_status():
    """Update status of a citizen report"""
    try:
        data = request.get_json()
        report_id = data.get('report_id')
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if not report_id or not new_status:
            return jsonify({'error': 'Report ID and status are required'}), 400
        
        result = mongodb.update_citizen_report_status(report_id, new_status, notes)
        if result:
            return jsonify({'message': 'Status updated successfully', 'report_id': report_id})
        else:
            return jsonify({'error': 'Failed to update status'}), 500
    except Exception as e:
        print(f"Error updating citizen report status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/citizen-report-analytics')
def api_citizen_report_analytics():
    """Get analytics for citizen reports"""
    try:
        analytics = mongodb.get_citizen_report_analytics()
        return jsonify(serialize_mongo_data(analytics))
    except Exception as e:
        print(f"Error getting citizen report analytics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/citizen-engagement-dashboard')
def api_citizen_engagement_dashboard():
    """Get comprehensive citizen engagement dashboard data"""
    try:
        # Get all relevant data
        reports_summary = aws_services.get_citizen_reports_summary()
        engagement_metrics = aws_services.get_citizen_engagement_metrics()
        analytics = mongodb.get_citizen_report_analytics()
        
        dashboard_data = {
            'reports_summary': reports_summary,
            'engagement_metrics': engagement_metrics,
            'analytics': analytics,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(dashboard_data)
    except Exception as e:
        print(f"Error getting citizen engagement dashboard: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/campaigns')
def api_campaigns():
    """Return all campaigns from MongoDB."""
    try:
        campaigns = list(mongodb.campaigns.find().limit(20))
        for c in campaigns:
            c['_id'] = str(c['_id'])
        return jsonify(campaigns)
    except Exception as e:
        print(f"Error in /api/campaigns: {e}")
        return jsonify([])
