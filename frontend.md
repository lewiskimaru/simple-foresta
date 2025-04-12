# Foresta - Frontend UI Documentation

## Technology Stack
*   **Framework:** React (v18+)
*   **Build Tool:** Vite
*   **Routing:** React Router (v6+)
*   **Styling:** Material UI (MUI) or Tailwind CSS (Choose one for consistency)
*   **State Management:** React Context API (for simple global state like auth) + React Query (for server state - API data fetching, caching, mutations)
*   **HTTP Client:** Axios
*   **Mapping:** React Leaflet or Mapbox React GL
*   **Charts:** Recharts or Chart.js (via react-chartjs-2)
*   **Forms:** React Hook Form (recommended for performance and validation) with Yup/Zod for schema validation.
*   **Date/Time:** date-fns or Day.js

## Overview
The Foresta frontend provides an interactive interface for users to manage conservation areas, monitor environmental data from satellites and sensors, and identify plant species. It features distinct layouts for unauthenticated users (landing, login, signup) and authenticated users (main dashboard, area-specific views).

## Core UI Structure

1.  **Unauthenticated Layout:**
    *   Simple header (Logo, Login/Sign Up buttons).
    *   Main content area displaying the current page (Landing, Login, Sign Up).
    *   Minimal footer.
2.  **Authenticated - Main Dashboard Layout:**
    *   **Top Bar:** Foresta Logo, "Add New Area" Button, Notifications Icon, User Profile Dropdown (Link to Profile, Logout).
    *   **Main Content Area:** Displays the list/grid of the user's conservation areas.
    *   **NO Sidebar.**
3.  **Authenticated - Area Detail Layout:**
    *   **Top Bar:** Same as Main Dashboard, potentially with the current Area Name displayed.
    *   **Sidebar (Persistent):** Navigation links:
        *   Home (Back to Main Dashboard - list of all areas)
        *   Area Home (Current Area's GEE/Map View)
        *   Species ID (Current Area's Identification Tool)
        *   Guardian (Current Area's Sensor Monitoring)
        *   --- Divider ---
        *   Settings (User Profile/Account Settings)
        *   Support
        *   Logout
    *   **Main Content Area:** Displays the selected section (Area Home, Species ID, Guardian) for the *currently active area*.

## Page Details

### 1. Landing Page (Public)
*   Route: `/`
*   Layout: Unauthenticated
*   Content:
    *   Hero section introducing Foresta and its mission.
    *   Sections describing key features (Area Management, GEE Insights, Species ID, Guardian Monitoring).
    *   Visuals (Illustrations, stock images).
    *   Call to action buttons ("Sign Up", "Learn More").

### 2. Login Page
*   Route: `/login`
*   Layout: Unauthenticated
*   Content:
    *   Foresta Logo. (its just the word "Foresta.")
    *   Form fields: Email, Password.
    *   "Log In" button.
    *   Links: "Forgot Password?", "Don't have an account? Sign Up".
    *   Handles authentication logic using API service, redirects to Main Dashboard on success. Displays errors on failure.

### 3. Sign Up Page
*   Route: `/signup`
*   Layout: Unauthenticated
*   Content:
    *   Foresta Logo.
    *   Form fields: Full Name, Email, Password, Confirm Password.
    *   Password strength indicator.
    *   Terms and Conditions checkbox/link.
    *   "Create Account" button.
    *   Link: "Already have an account? Log In".
    *   Handles registration using API service, potentially redirects to Login or Main Dashboard on success. Displays errors.

### 4. User Profile Page
*   Route: `/profile` or `/settings/account`
*   Layout: Area Detail Layout (Accessed via Sidebar/Top Bar Menu)
*   Content:
    *   User info display (Name, Email).
    *   Sections/Tabs for:
        *   Update Profile Info (Name)
        *   Change Password
        *   Notification Preferences (if implemented)
        *   Account Deletion (with confirmation)

### 5. Main Dashboard (User's Area List)
*   Route: `/dashboard` (or similar home route for authenticated users)
*   Layout: Authenticated - Main Dashboard Layout (Top Bar only)
*   Content:
    *   Heading: "My Conservation Areas".
    *   "Add New Area" button (triggers Add Area Modal/Flow).
    *   Grid or list display of areas created by the logged-in user. Each item should show:
        *   Area Name
        *   Small thumbnail/placeholder image (optional, static initially ok)
    *   Clicking an area item navigates to the Area Detail View (`/areas/<area_id>/home`).
    *   Displays a message if the user has no areas yet, prompting them to create one.
    *   Fetches area list from backend (`/api/areas`).

### 6. Add New Area Process (Modal/Form)
*   Triggered from Main Dashboard.
*   Not a separate page, likely a Modal overlay or inline form.
*   Steps:
    1.  Input field for "Area Name/Search Term".
    2.  User types, triggers API call to frontend service wrapping OSM Nominatim search (debounced for performance).
    3.  Displays list of potential location matches below input.
    4.  User clicks a result.
    5.  Frontend sends selected location data (Name, OSM ID, Type) to backend endpoint (`/api/areas`).
    6.  Displays loading indicator while backend processes (fetches boundaries, saves).
    7.  On success: Close modal, refresh area list on Main Dashboard.
    8.  On error: Display error message in the modal.

### 7. Area Detail - Home Page
*   Route: `/areas/<area_id>/home` (or `/areas/<area_id>`)
*   Layout: Authenticated - Area Detail Layout (Top Bar + Sidebar)
*   Content:
    *   Area Name prominently displayed (maybe in Top Bar or as page heading).
    *   **GEE Insights Widgets:**
        *   Widget/Card: Tree Loss % (displaying `gee_tree_loss_percentage` from backend).
        *   Widget/Card: Tree Gain % (displaying `gee_tree_gain_percentage`).
        *   Widget/Chart: Deforestation Trends Graph (using `gee_deforestation_trends` JSON data from backend, plotted with Recharts/Chart.js).
    *   **Area Map Widget:**
        *   Interactive Map (Leaflet/Mapbox).
        *   Displays the area boundary polygon (fetched from `boundary_coordinates` in backend). Map should zoom/center on the boundary.
        *   Displays markers/pins for each Guardian sensor associated with this area (fetching sensor list with coordinates from `/api/areas/<area_id>/sensors`).
        *   Clicking a sensor pin could show a small popup with basic info (Name, Status).
    *   Fetches Area details (including GEE data, boundaries) and Sensor list from backend.

### 8. Area Detail - Species ID Page
*   Route: `/areas/<area_id>/species`
*   Layout: Authenticated - Area Detail Layout (Top Bar + Sidebar)
*   Content:
    *   Heading: "Identify Species".
    *   **Upload Area:**
        *   Drag-and-drop zone or file input button for image upload.
        *   Accepts standard image formats (JPG, PNG).
        *   Maybe basic instructions (e.g., "Upload clear image of leaf, flower, or bark").
    *   **Identification Result Display:**
        *   Shows loading state while PlantNet API is called.
        *   On success: Displays the raw JSON response from PlantNet in a formatted code block or structured view. Highlights key info like Best Match, Score, Common Names.
        *   On error: Displays error message from PlantNet or network error.
    *   **Identification History:**
        *   Heading: "Past Identifications in this Area".
        *   List/Grid displaying past identification records for *this specific area* and *this user*.
        *   Each item shows:
            *   Thumbnail of the uploaded image (fetched from `image_url` stored in backend).
            *   Best Match Species Name.
            *   Identification Score.
            *   Timestamp.
            *   Option to view full JSON result again (modal?).
        *   Fetches history from backend (`/api/areas/<area_id>/species/history`) with pagination.

### 9. Area Detail - Guardian Monitoring Page
*   Route: `/areas/<area_id>/guardian`
*   Layout: Authenticated - Area Detail Layout (Top Bar + Sidebar)
*   Content:
    *   Heading: "Guardian Sensor Monitoring".
    *   **Recent Alerts Panel:**
        *   List of recent alerts (fire, logging, low battery, etc.) for sensors *in this area*.
        *   Shows Timestamp, Alert Type, Sensor Name/ID, Status (New/Acknowledged).
        *   Filter options (Type, Date Range).
        *   Action buttons (Acknowledge/Resolve - triggers backend API calls).
        *   Fetches from `/api/areas/<area_id>/alerts`. Real-time updates via WebSockets would be ideal, fallback to polling.
    *   **Active Sensors Overview:**
        *   Summary cards: Total Sensors, Online Count, Offline Count.
        *   Maybe a list/table of sensors in the area: Name, Status, Last Seen, Battery %.
        *   Fetches from `/api/areas/<area_id>/sensors`.
    *   **(Optional) Sensor-Focused Map:** Could repeat the map from Area Home, but potentially with more sensor-specific interactions or layers (e.g., color-coding pins by status).
    *   **Data Trends Charts:**
        *   Line charts showing historical data for key metrics across sensors in the area (or selectable per sensor).
        *   Examples: Average Temperature Trend (last 24h/7d), Average Humidity Trend.
        *   Requires backend endpoint(s) to provide aggregated/historical sensor readings (e.g., `/api/areas/<area_id>/sensors/readings?metric=temperature&period=24h`).

### 10. Settings Page
*   Route: `/settings` (or sub-routes like `/settings/profile`, `/settings/notifications`)
*   Layout: Authenticated - Area Detail Layout (Top Bar + Sidebar) - Content depends on the specific settings section being viewed (e.g., User Profile form).

### 11. Support Page
*   Route: `/support`
*   Layout: Authenticated - Area Detail Layout (Top Bar + Sidebar)
*   Content:
    *   FAQ Section.
    *   Contact Form (sends email or creates support ticket via backend API).
    *   Link to documentation (if available).

## UI Design Elements

*   **Color Scheme:**
    *   Primary: `#169014` (Side menu background, icons, active elements)
    *   Secondary: `#e1ecd9` (Widget backgrounds, secondary buttons)
    *   Accent: `#87d685` (Hover states, highlighted buttons, success indicators)
    *   Neutral: `#FFFFFF`, `#F5F5F5` (Page backgrounds), `#333333` (Primary text), `#666666` (Secondary text)
    *   Alerts: Red (`#D32F2F`), Warnings: Orange (`#FFA000`), Info: Blue (`#1976D2`)
*   **Typography:**
    *   Use a clean sans-serif font (e.g., Roboto, Inter, Open Sans) via Google Fonts or similar.
    *   Clear hierarchy: Larger/bolder fonts for headings (e.g., `h1`, `h2`), standard weight/size for body text, smaller/lighter for secondary info.
    *   Ensure good readability and contrast.
*   **Iconography:**
    *   Use a consistent icon set (e.g., Material Icons, Font Awesome, or custom icons).
    *   Use icons intuitively (e.g., gear for settings, bell for notifications, leaf for species, map-marker for location).
*   **Layout:**
    *   Use MUI Grid system or Tailwind CSS classes for responsive layouts.
    *   Ensure components adapt gracefully to different screen sizes (desktop, tablet, mobile).
    *   Sidebar should collapse or become a drawer on smaller screens.

## Interactions and States

*   **Loading States:** Use spinners or skeleton screens (MUI provides these) when fetching data (area list, GEE data, history, sensor data). Disable buttons during API calls.
*   **Error States:** Display clear, user-friendly error messages within components or using toast notifications (e.g., using `react-toastify` or MUI Snackbar) when API calls fail.
*   **Empty States:** Provide informative messages when lists are empty (e.g., "No areas created yet", "No identification history", "No active alerts").
*   **Feedback:** Use visual feedback for actions (e.g., button click effects, confirmation messages after saving/deleting).
*   **Real-time Updates (Optional but Recommended):** Use WebSockets (with Socket.IO client) to receive real-time alerts and sensor status updates from the backend and update the UI without needing manual refresh. Fallback to periodic polling if WebSockets are not implemented.

## Technical Integration Points

*   **API Service Layer:** Centralize Axios calls in `/src/services`. Create instances configured with the `VITE_API_BASE_URL`. Include interceptors to automatically add the JWT `Authorization` header.
*   **Environment Variables:** Use `.env` file for API base URLs (`VITE_API_BASE_URL`) and public keys (`VITE_PLANTNET_API_KEY`). **Never commit sensitive keys directly into code.**
*   **Authentication Flow:** Implement logic in components/hooks to call login/signup API endpoints, store/retrieve JWT tokens (securely!), handle token expiration (redirect to login or use refresh tokens), and conditionally render routes/components based on auth status.
*   **Mapping Library Integration:** Configure React Leaflet/Mapbox properly. Handle asynchronous loading of boundary/sensor data before rendering map layers.
*   **Charting Library Integration:** Pass data fetched from the backend to Recharts/Chart.js components in the expected format.
