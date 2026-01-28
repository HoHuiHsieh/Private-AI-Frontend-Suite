# AppProvider Context

## 1. Purpose
The AppProvider context manages global application state, navigation, and configuration throughout the webui.

## 2. Requirements
- Global application state management
- Navigation state tracking
- Application configuration
- Theme and UI state management
- Cross-component communication

## 3. Design
- **Context**: React Context API implementation
- **Provider**: AppProvider component wrapping the app
- **State**: Application navigation, settings, configuration
- **Actions**: Navigation updates, setting changes

## 4. State Structure

### Navigation State
- **selectedItem**: Currently selected menu item
- **selectedApp**: Currently active application (home, openai-platform, chatbot)
- **menuOpen**: Sidebar menu visibility state

### Application Settings
- **theme**: Current theme configuration
- **language**: Application language setting
- **preferences**: User preference settings

### Configuration
- **apiBaseUrl**: Backend API base URL
- **features**: Enabled feature flags
- **version**: Application version information

## 5. Key Functions

### Navigation
- **setSelectedItem(item)**: Update selected menu item
- **setSelectedApp(app)**: Switch between applications
- **toggleMenu()**: Toggle sidebar menu visibility

### Configuration
- **updateSettings(settings)**: Update application settings
- **setTheme(theme)**: Change application theme
- **setLanguage(lang)**: Change application language

## 6. Integration
- Wraps the main application components
- Used by ViewPort for navigation
- Provides state to all menu components
- Manages application-wide configuration