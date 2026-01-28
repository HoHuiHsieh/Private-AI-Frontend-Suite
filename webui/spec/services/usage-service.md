# Usage Service

## 1. Purpose
The usage service provides access to usage statistics, monitoring data, and system health information for users and administrators.

## 2. Requirements
- User usage statistics and charts
- System-wide usage monitoring
- Health metrics and GPU status
- Model usage breakdown
- Time-based filtering and aggregation

## 3. Design
- **API Endpoints**: /api/usage/* and /api/admin/health/*
- **Data Visualization**: Integration with charting libraries
- **Permission Levels**: User and admin access levels
- **Time Filtering**: Date range and interval parameters

## 4. Key Functions

### User Usage
- **getUsageOverview(params)**: Get user's usage statistics
- **getUsageByModel(params)**: Model-specific usage data
- **getUsageLogs(params)**: Detailed usage logs with pagination

### Admin Health
- **getSystemOverview(params)**: System-wide health metrics
- **getSystemModelUsage(params)**: All users' model usage
- **getGPUStatus()**: GPU monitoring data

### Data Features
- **Aggregation**: Sum tokens and requests by time periods
- **Filtering**: Date ranges, intervals, user-specific data
- **Visualization**: Chart-ready data formats

## 5. Integration
- Used by usage dashboard in OpenAI Platform
- Integrated with admin health monitoring
- Provides data for charts and statistics displays