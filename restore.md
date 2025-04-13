# Restore Feature Documentation

## Overview
The Restore page within the Foresta application allows conservation officials to plan, track, and manage restoration activities for areas of interest. It provides a comprehensive interface for recording both planned and completed restoration efforts, with a focus on metrics tracking and activity management.

## Page Structure and Design

### Header Section
- **Metrics Dashboard**: Horizontal cards showing key metrics:
  - Trees Planted: [count]
  - Total Area Restored: [hectares]
  - Seeds Dispersed: [count]
  - Survival Rate: [percentage]
  - Species Count: [count]

### Main Content

#### Tab Navigation
- **Planned Activities** (default tab)
- **Completed Activities**
- **All Activities**

#### Activity Cards Grid/List
- Filterable by date range, species, and status
- Each card displays:
  - Activity name
  - Date/timeline
  - Status indicator (planned, in progress, completed)
  - Then on hover it shows
    - Type (seeding, planting, maintenance)
    - Species count and primary species
    - Team size/volunteer count
    - Quick action buttons (edit, delete, mark complete)

### Floating Action Button
- "+" button to add new restoration activity

## New Restoration Activity Form

### Form Structure (Modal or Slide-in Panel, this is a multi step form)

#### Basic Information Section
- **Activity Name**: Text field (e.g., "North Ridge Planting")
- **Activity Type**: Dropdown (Planting, Seeding, Maintenance, Monitoring)
- **Start Date**: Date picker
- **End Date**: Date picker (optional)
- **Status**: Dropdown (Planned, In Progress, Completed)
- **Description**: Text area

#### Location Definition
- **Size**: Manual entry (hectares/acres)
- **Terrain Type**: Dropdown (Open field, Partial canopy, Steep slope, Riparian, etc.)
- **Soil Type**: Dropdown (Clay, Loam, Sandy, etc.)

#### Species Section
- **Add Species**: Multi-entry form with:
  - Species dropdown (from existing species database)
  - Quantity field (for seeds or seedlings)
  - Source field (nursery name, wild collection, etc.)
  - Expected survival rate (%)
  - Add button to include another species

#### Planting Method Section
- **Method**: Dropdown (Manual planting, Mechanical seeding, Drone seed dispersal, Natural regeneration)
- **Method Details**: Text area that changes based on selected method
  - For drone dispersal: flight pattern, altitude, dispersal rate
  - For manual planting: spacing, planting depth
  - For mechanical seeding: equipment type, seeding density

#### Resources Section
- **Team Size**: Number input
- **Volunteer Count**: Number input
- **Equipment**: Multi-select checkboxes (Shovels, Watering equipment, Drones, etc.)
- **Budget**: Currency input
- **Funding Source**: Text field

#### Success Metrics Section
- **Success Criteria**: Text area or structured inputs
- **Monitoring Schedule**: Dropdown (Weekly, Monthly, Quarterly, Annually)
- **Expected Outcomes**: Text area
- **Notes**: Text area

### Form Bottom Actions
- **Cancel**: Closes form without saving
- **Save as Draft**: Saves as planned activity
- **Submit**: Creates the activity and returns to main view

## User Flow

1. **Accessing the Restore Page**
   - User navigates to an area's dashboard
   - User clicks on "Restore" in the sidebar navigation

2. **Viewing Activities**
   - User is presented with the default "Planned Activities" tab
   - User can switch between tabs to view different activity statuses
   - User can filter activities by date range, species, or other criteria
   - User can click on an activity card to view full details

3. **Creating a New Activity**
   - User clicks the "+" floating action button
   - The new activity form appears as a modal or slide-in panel
   - User fills in required information across all sections
   - User clicks "Submit" to create the activity or "Save as Draft" to save it for later

4. **Managing Existing Activities**
   - User can edit activity details by clicking the edit button on an activity card
   - User can delete an activity by clicking the delete button (with confirmation)
   - User can mark a planned activity as "In Progress" or "Completed" using the status dropdown

5. **Monitoring Metrics**
   - Metrics at the top of the page automatically update based on activity data
   - User can view detailed breakdowns by clicking on a metric card

## Database Schema

### RestoreActivity
- `id` (PK): Integer
- `area_id` (FK): Integer (references Area.id)
- `name`: String
- `type`: String (Enum: "Planting", "Seeding", "Maintenance", "Monitoring")
- `status`: String (Enum: "Planned", "In Progress", "Completed")
- `start_date`: DateTime
- `end_date`: DateTime (nullable)
- `description`: Text
- `size`: Float (hectares)
- `terrain_type`: String
- `soil_type`: String
- `planting_method`: String (Enum: "Manual", "Mechanical", "Drone", "Natural")
- `method_details`: JSON
- `team_size`: Integer
- `volunteer_count`: Integer
- `equipment`: Array/JSON
- `budget`: Float
- `funding_source`: String
- `success_criteria`: Text
- `monitoring_schedule`: String
- `expected_outcomes`: Text
- `notes`: Text
- `created_at`: DateTime
- `updated_at`: DateTime
- `created_by`: Integer (FK to User.id)

### RestoreActivitySpecies
- `id` (PK): Integer
- `activity_id` (FK): Integer (references RestoreActivity.id)
- `species_id` (FK): Integer (references Species.id)
- `quantity`: Integer
- `source`: String
- `expected_survival_rate`: Float
- `notes`: Text

### RestoreMetrics (Optional - can be calculated on the fly)
- `id` (PK): Integer
- `area_id` (FK): Integer (references Area.id)
- `trees_planted`: Integer
- `area_restored`: Float
- `seeds_dispersed`: Integer
- `survival_rate`: Float
- `species_count`: Integer
- `calculated_at`: DateTime

## API Endpoints

### Restoration Activities
- `GET /api/areas/:id/restore/activities`: List all restoration activities for an area
- `GET /api/areas/:id/restore/activities?status=:status`: Filter activities by status
- `POST /api/areas/:id/restore/activities`: Create new restoration activity
- `GET /api/restore/activities/:id`: Get single activity details
- `PUT /api/restore/activities/:id`: Update activity
- `DELETE /api/restore/activities/:id`: Delete activity
- `PATCH /api/restore/activities/:id/status`: Update activity status

### Restoration Metrics
- `GET /api/areas/:id/restore/metrics`: Get restoration metrics for an area

## Data Flow

### Activity Creation
1. User submits form with activity details
2. Frontend sends data to backend via POST request
3. Backend validates data and creates new activity record
4. Backend creates related species records
5. Backend recalculates area metrics
6. Frontend refreshes activity list and metrics display

### Activity Update
1. User modifies activity details
2. Frontend sends updated data to backend
3. Backend updates activity record
4. Backend updates related species records if changed
5. Backend recalculates area metrics if needed
6. Frontend refreshes display with updated information

### Metrics Calculation
Metrics are calculated by aggregating data from all completed restoration activities:
- Trees Planted: Sum of quantities from RestoreActivitySpecies for completed planting activities
- Area Restored: Sum of size fields from completed RestoreActivity records
- Seeds Dispersed: Sum of quantities from RestoreActivitySpecies for completed seeding activities
- Survival Rate: Weighted average based on quantity and expected_survival_rate
- Species Count: Count of distinct species_id values across all activities
