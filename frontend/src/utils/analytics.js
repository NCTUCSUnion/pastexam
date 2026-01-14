/**
 * Analytics utility for tracking user events
 * Uses Umami analytics for event tracking
 */

/**
 * Track a custom event
 * @param {string} eventName - Name of the event
 * @param {object} eventData - Optional event data/properties
 */
export const trackEvent = (eventName, eventData = {}) => {
  try {
    // Check if umami is available
    if (typeof window !== 'undefined' && window.umami) {
      window.umami.track(eventName, eventData)
      //   console.log('Event tracked:', eventName, eventData)
    } else {
      //   console.warn('Umami not loaded, event not tracked:', eventName, eventData)
    }
  } catch (error) {
    console.error('Error tracking event:', error, eventName, eventData)
  }
}

/**
 * Track page view
 * @param {string} pageName - Name of the page
 */
export const trackPageView = (pageName) => {
  trackEvent('pageview', { page: pageName })
}

// Pre-defined event names for consistency
export const EVENTS = {
  // Theme events
  TOGGLE_THEME: 'toggle-theme',

  // Auth events
  LOGIN: 'login',
  LOGOUT: 'logout',
  LOGIN_OAUTH: 'login-oauth',
  LOGIN_LOCAL: 'login-local',

  // Navigation events
  TOGGLE_SIDEBAR: 'toggle-sidebar',
  NAVIGATE_HOME: 'navigate-home',
  NAVIGATE_ARCHIVE: 'navigate-archive',
  NAVIGATE_ADMIN: 'navigate-admin',

  // Archive events
  VIEW_ARCHIVE: 'view-archive',
  DOWNLOAD_ARCHIVE: 'download-archive',
  PREVIEW_ARCHIVE: 'preview-archive',
  UPLOAD_ARCHIVE: 'upload-archive',
  EDIT_ARCHIVE: 'edit-archive',
  DELETE_ARCHIVE: 'delete-archive',
  GENERATE_AI_EXAM: 'generate-ai-exam',
  SEARCH_COURSE: 'search-course',
  SELECT_COURSE: 'select-course',
  FILTER_ARCHIVES: 'filter-archives',

  // Admin events
  CREATE_COURSE: 'create-course',
  UPDATE_COURSE: 'update-course',
  DELETE_COURSE: 'delete-course',
  CREATE_USER: 'create-user',
  UPDATE_USER: 'update-user',
  DELETE_USER: 'delete-user',
  CREATE_NOTIFICATION: 'create-notification',
  UPDATE_NOTIFICATION: 'update-notification',
  DELETE_NOTIFICATION: 'delete-notification',
  OPEN_NOTIFICATION_CENTER: 'open-notification-center',

  // Issue report events
  OPEN_ISSUE_REPORT: 'open-issue-report',
  SUBMIT_ISSUE_REPORT: 'submit-issue-report',

  // Tab/Panel events
  SWITCH_TAB: 'switch-tab',

  // Navbar events
  OPEN_MORE_ACTIONS_MENU: 'open-more-actions-menu',

  // Discussion events
  DISCUSSION_SEND_MESSAGE: 'discussion-send-message',
  DISCUSSION_UPDATE_NICKNAME: 'discussion-update-nickname',
  DISCUSSION_SET_DEFAULT_OPEN: 'discussion-set-default-open',
}
