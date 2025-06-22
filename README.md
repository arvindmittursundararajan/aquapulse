# AquaPulse: Smart Algae Bloom Detection and Prediction

## Overview

AquaPulse is a next-generation, cloud-native solution for real-time harmful algae bloom (HAB) monitoring, analytics, and citizen engagement. It leverages AWS generative AI, IoT, and advanced cloud services to deliver actionable insights, automate response, and empower communities and authorities to drive measurable environmental impact.

---

## AWS Services Utilized

### **Core Generative AI & ML**
- **Amazon Bedrock**: Foundation for real-time anomaly detection, root cause analysis, and generation of actionable recommendations. Powers explainable AI, multi-agent optimization, and natural language summaries across all operational and citizen-facing modules.
- **Amazon SageMaker**: Drives advanced analytics, forecasting, and scenario modeling for microplastics, lifecycle analysis, and global impact. Enables ML-driven decision support and predictive insights.

### **Conversational & Multimodal AI**
- **Amazon Lex**: Provides conversational AI for chatbots, enabling natural language citizen engagement, report submission, and information retrieval.
- **Amazon Transcribe**: Converts voice reports and audio input into text, supporting accessible, voice-driven reporting and engagement.
- **Amazon Polly**: Synthesizes AI-generated insights and alerts into speech, making the platform accessible to users with varying literacy or physical abilities.

### **Data, Connectivity, and Orchestration**
- **AWS IoT Core**: Ingests real-time sensor data from distributed IoT devices, enabling live hotspot detection, predictive analytics, and automated response.
- **AWS Lambda**: Orchestrates event-driven processing, automation, and integration between AI, IoT, and data storage components.
- **Amazon S3**: Serves as the data lake for sensor data, reports, analytics outputs, and downloadable resources.
- **Amazon Rekognition**: Analyzes uploaded images for plastic waste, supporting multi-modal citizen reporting and automated validation.
- **Amazon SNS**: (If enabled) Delivers real-time notifications and alerts to stakeholders.
- **AWS IAM**: Manages secure, role-based access for all AWS resources and automation.
- **Bedrock Agent (Multi-Agent AI)**: Coordinates complex, multi-step optimization and decision support workflows, including resource allocation, mission planning, and explainable recommendations.

---

## Business & Societal Impact

- **Real-Time Environmental Intelligence**: Fuses IoT, 5G/edge, and generative AI to deliver live, actionable insights for pollution detection, cleanup, and prevention.
- **Equitable Digital Access**: Democratizes environmental data and AI-driven recommendations through voice, chat, and accessible UI, bridging digital divides.
- **Measurable Outcomes**: Tracks pollution reduction, cleanup effectiveness, citizen engagement, and operational efficiency with transparent, data-driven metrics.
- **Scalable & Extensible**: Modular architecture supports rapid adaptation to new domains (healthcare, education, sustainability, etc.) and geographies.

---

## User Experience & Accessibility

- **Modern, Minimalist UI**: Responsive, intuitive dashboards and modals for all user types.
- **Multi-Modal Interaction**: Supports chat, voice, and image-based reporting and engagement.
- **Accessibility**: Designed for users with varying digital literacy and physical abilities, including voice input/output and mobile optimization.
- **Guided Workflows**: Contextual help, tooltips, and clear navigation for seamless user journeys.

---

## Technical Excellence

- **Cloud-Native, Event-Driven**: Robust, scalable backend with modular service layers and real-time data flows.
- **Error Handling & Reliability**: Comprehensive error management, logging, and fallback mechanisms ensure uptime and data integrity.
- **Well-Documented & Maintainable**: Consistent code structure, inline documentation, and clear API contracts.
- **No Demo Data**: All features operate on real, production-grade data from AWS and MongoDB.

---

## Evaluation Criteria (with Business/Technical Answers)

### 1. **Thorough Use of AWS Generative AI**
- Bedrock and SageMaker are deeply integrated, powering core analytics, recommendations, and optimization. Generative AI is foundational, not an add-on.

### 2. **Core Integration of Bedrock/SageMaker/Q**
- Bedrock: AI-driven alerts, explainable recommendations, multi-agent optimization.
- SageMaker: ML analytics for microplastics, lifecycle, and impact forecasting.

### 3. **Combining Generative AI with Next-Gen Connectivity**
- IoT/5G sensor data is processed and analyzed by Bedrock/SageMaker in real time, enabling live detection and automated response.

### 4. **Telecom & AI for Equitable Digital Experience**
- IoT/5G extends reach to underserved areas; AI/voice/chat interfaces ensure accessibility for all users.

### 5. **Measurable, Significant Real-World Impact**
- Environmental, societal, and operational metrics are tracked and surfaced in dashboards for transparent impact assessment.

### 6. **Societal Problem & Measurable Change**
- Directly addresses plastic pollution, empowering communities and authorities with actionable intelligence and participatory tools.

### 7. **Clean, Intuitive, Accessible UI**
- Minimalist, responsive design with multi-modal input and accessibility features.

### 8. **User Experience for Diverse Audiences**
- Voice/chat/image support, contextual help, and mobile optimization ensure usability for all.

### 9. **Robust, Well-Engineered Implementation**
- Modular, scalable, and cloud-native backend; maintainable, decoupled frontend; comprehensive error handling.

### 10. **High-Quality, Well-Documented Codebase**
- Consistent structure, inline docs, reliable operation, and reproducible deployment.

### 11. **Creativity, Uniqueness, and Improvement**
- Unifies generative AI, IoT, and citizen engagement in a single, explainable, and participatory platform.

### 12. **Novelty vs. Existing Solutions**
- Advances the state of the art by combining real-time IoT, generative AI, and participatory action, with explainable, actionable insights and equitable access.

---

## Summary Table: AWS Service Mapping

| Modal/Screen           | IoT | Lambda | Bedrock | S3 | SageMaker | Lex | Transcribe | Rekognition | Polly | SNS | Agent |
|------------------------|-----|--------|---------|----|-----------|-----|------------|-------------|-------|-----|-------|
| Hotspot Detection      | ✅  | ✅     | ✅      | ✅ |           |     |            |             |       |     |       |
| Microplastics Analytics|     | ✅     |         | ✅ | ✅        |     |            |             |       |     |       |
| Cleanup Missions       | ✅  | ✅     |         | ✅ |           |     |            |             |       |     | ✅    |
| Citizen Reports        |     | ✅     | ✅      | ✅ |           | ✅  | ✅         | ✅          | ✅    |     |       |
| AI Alerts              |     | ✅     | ✅      | ✅ |           |     |            |             | ✅    | ✅  |       |
| Data Lake Insights     |     | ✅     |         | ✅ | ✅        |     |            |             |       |     |       |
| Plastic Lifecycle      |     |        | ✅      | ✅ | ✅        |     |            |             |       |     |       |
| Global Impact          |     |        | ✅      | ✅ | ✅        |     |            |             |       |     |       |
| Engage                |     | ✅     |         | ✅ |           | ✅  |            |             |       | ✅  |       |

---

## Why This Solution is Unique

- **End-to-End Intelligence**: From sensor to insight to action, every step is automated, explainable, and participatory.
- **Equitable Access**: Designed for all users, regardless of digital literacy or connectivity.
- **Scalable Impact**: Modular, cloud-native, and ready for global deployment and adaptation.
- **Transparent & Measurable**: Every action, insight, and outcome is tracked and reported for maximum accountability and learning.

---

## Getting Started

1. Clone the repository and install dependencies (`pip install -r requirements.txt`).
2. Configure your AWS credentials and MongoDB connection in `config.py`.
3. Run the Flask app (`python app.py`).
4. Access the dashboard at `http://localhost:5000` and explore all features.

---

For more details, see the in-code documentation and the AWS Service Mapping HTML for a visual overview of all integrations.

## Features

AquaPulse provides a comprehensive, production-grade platform for harmful algae bloom (HAB) detection, prediction, and response. Every feature is powered by real data and deeply integrated with AWS services. The platform includes:

### Dashboard & Metrics
- **Live Metrics:** Real-time display of active sensors, high algae bloom events, active mitigation missions, and biomass collected (kg).
- **Global Algae Bloom Map:** Interactive map with live sensor overlays, color-coded by algae bloom severity, with legend and layer toggling.
- **AI Neural Network Analysis:** Real-time, Bedrock-powered HTML insights on location-wise algae bloom levels, microalgae concentration, and status alerts, with voice playback (Polly).
- **Algae Bloom Predictions:** SageMaker-driven prediction charts for current, 7-day, and 30-day algae bloom trends by region.
- **Autonomous Mitigation Coordination:** Live status of ocean drones, surface vessels, underwater units, and next deployment location.

### Operations Center Modals
- **Hotspot Detection:** Map and list of critical algae bloom hotspots, with AWS IoT/Lambda/Bedrock integration and downloadable data.
- **Microalgae Analytics:** Deep analytics on microalgae concentration by location, with ML-driven charts, data explorer, and downloadable reports.
- **Mitigation Missions:** Status and details of all active mitigation missions, robot deployment, daily stats, and mission logs.
- **Citizen Reports:** List and statistics of citizen-submitted algae bloom reports, with severity, type, and status breakdowns.
- **AI Alerts:** Bedrock-generated, actionable alerts with severity, location, recommended actions, and summary statistics.
- **Data Lake Insights:** S3-powered analytics on all stored data, including file counts, size, monitored locations, date range, cleanup effectiveness, and pollution trends.
- **Algae Bloom Lifecycle:** Analysis of algae bloom lifecycle stages, global statistics, and recommended interventions.
- **Global Impact:** Regional and global impact assessment, including oceans affected, marine species at risk, economic cost, and AI recommendations.
- **Engage:** Opportunities for citizen, organization, and government engagement, plus success stories and impact metrics.

### Multi-Modal Reporting & Accessibility
- **Voice Reporting:** Submit algae bloom reports via voice, transcribed and analyzed using Transcribe, Lex, and Bedrock.
- **Chatbot Support:** Natural language chat interface for reporting, queries, and help, powered by Lex and Bedrock.
- **Image Analysis:** Upload images for automated algae bloom detection using Rekognition.
- **Accessible UI:** All features are accessible via keyboard, screen reader, and mobile devices. Voice output via Polly.

### AWS Service Management & Automation
- **IoT Device Management:** Create, list, and manage IoT sensors for algae bloom monitoring.
- **Lambda Function Management:** Create and manage Lambda functions for data processing, cleanup coordination, and alerting.
- **Data Lake Management:** Create S3 buckets, upload data, and manage backups.
- **IAM Role Management:** Create and list IAM roles for secure AWS integration.
- **SageMaker Model Management:** List and manage SageMaker models for ML analytics.
- **Comprehensive AWS Status:** View live status of all AWS services powering the platform.
- **Demo Data/Service Reset:** Delete and recreate demo services and data for testing and onboarding.

### API Endpoints
- **/api/sensor-data:** Get all sensor/device data (IoT/MongoDB).
- **/api/predictions:** Get algae bloom prediction data (SageMaker/MongoDB).
- **/api/cleanup-status:** Get mitigation mission and cleanup data.
- **/api/analyze-image:** Analyze uploaded images for algae bloom (Rekognition).
- **/submit-report:** Submit new algae bloom report (form, voice, or image).
- **/api/aws-services-status:** Get status of all AWS services.
- **/api/iot-sensors:** List all IoT sensors.
- **/api/publish-iot-message:** Publish message to IoT topic.
- **/api/upload-pollution-data:** Upload sensor/report data to S3.
- **/api/create-backup:** Create backup snapshot of S3 data.
- **/api/data-analytics/<bucket_name>:** Get analytics on stored data.
- **/api/lex-interaction:** Process chatbot/voice interaction (Lex/Bedrock).
- **/api/delete-junk-services:** Delete all test/demo AWS resources.
- **/api/citizen-reports:** Get all citizen reports.
- **/api/engage-actions:** Get engagement actions and opportunities.
- **/api/microplastics-analytics:** Get microalgae analytics data.
- **/api/iam-roles:** List IAM roles.
- **/api/create-iam-role:** Create IAM role.
- **/api/sagemaker-models:** List SageMaker models.
- **/api/global-impact:** Get global impact statistics and predictions.
- **/api/ai-analysis:** Get Bedrock-powered AI analysis for dashboard.
- **/api/ai-alerts:** Get Bedrock-powered AI alerts.
- **/api/cleanup-missions:** Get mitigation mission data.
- **/api/data-lake-insights:** Get S3-powered data lake insights.
- **/api/plastic-lifecycle:** Get algae bloom lifecycle data.
- **/api/citizen-reports-summary:** Get summary of citizen reports.
- **/api/campaigns:** Get all engagement campaigns.

## Reusable AWS Service Example Scripts

AquaPulse includes a suite of reusable Python scripts for AWS integration, prototyping, and testing. These are located in the `aws_service_boto_examples` folder and demonstrate best practices for interacting with AWS services using Boto3. Each script is ready for adaptation to your own projects or for rapid experimentation.

| Script Name                | Description                                                      |
|---------------------------|------------------------------------------------------------------|
| **mongodb_example.py**         | MongoDB Atlas connection and operations example                  |
| **transcribe_example.py**      | Amazon Transcribe audio transcription example                    |
| **sagemaker_example.py**       | Amazon SageMaker model management and inference example          |
| **s3_example.py**              | Amazon S3 bucket and object management example                   |
| **rekognition_example.py**     | Amazon Rekognition image analysis example                        |
| **lex_example.py**             | Amazon Lex chatbot and conversational AI example                 |
| **bedrock_example.py**         | Amazon Bedrock generative AI model invocation example            |
| **iot_example.py**             | AWS IoT Core device and message management example               |
| **polly_example.py**           | Amazon Polly text-to-speech example                              |
| **lambda_example.py**          | AWS Lambda function management and invocation example            |
| **bedrock_agent_example.py**   | Amazon Bedrock Agent orchestration and multi-agent workflow      |
| **api_test_example.py**        | Example for testing API endpoints and integrations               |

> **Tip:** Configure your AWS credentials and environment variables as needed. These scripts are designed for rapid prototyping, learning, and can be adapted for production use.
