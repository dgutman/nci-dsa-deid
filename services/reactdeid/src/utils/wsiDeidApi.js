/**
 * WSI DeID API Helper Functions
 * 
 * This module provides helper functions for interacting with the WSI DeID API endpoints.
 * All functions require authentication headers which should be obtained from useDsaAuth hook.
 */

/**
 * Get the base URL for WSI DeID endpoints
 * @param {string} apiBaseUrl - The base DSA API URL
 * @returns {string} The WSI DeID API base URL
 */
export const getWsiDeIdBaseUrl = (apiBaseUrl) => {
  // Remove /api/v1 if present, then add /wsi_deid
  let base = apiBaseUrl
  if (base.endsWith('/api/v1')) {
    base = base.replace('/api/v1', '')
  } else if (base.endsWith('/api/v1/')) {
    base = base.replace('/api/v1/', '')
  }
  return `${base}/wsi_deid`
}

// ============================================================================
// Bulk Actions
// ============================================================================

/**
 * Refile multiple images at once
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {object} data - Request body with items to refile
 * @returns {Promise<Response>}
 */
export const bulkRefile = async (apiBaseUrl, headers, data) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/action/bulkRefile`, {
    method: 'PUT',
    headers: {
      ...headers,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
}

/**
 * Export recently finished items to the export folder
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @returns {Promise<Response>}
 */
export const exportRecent = async (apiBaseUrl, headers) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/action/export`, {
    method: 'PUT',
    headers
  })
}

/**
 * Export all finished items to the export folder
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @returns {Promise<Response>}
 */
export const exportAll = async (apiBaseUrl, headers) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/action/exportall`, {
    method: 'PUT',
    headers
  })
}

/**
 * Generate a report of the items in the system
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @returns {Promise<Response>}
 */
export const exportReport = async (apiBaseUrl, headers) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/action/exportreport`, {
    method: 'PUT',
    headers
  })
}

/**
 * Ingest data from the import folder
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @returns {Promise<Response>}
 */
export const ingest = async (apiBaseUrl, headers) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/action/ingest`, {
    method: 'PUT',
    headers
  })
}

/**
 * Perform an action on a list of items
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {string} action - Action name
 * @param {object} data - Request body with item list
 * @returns {Promise<Response>}
 */
export const listAction = async (apiBaseUrl, headers, action, data) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/action/list/${action}`, {
    method: 'PUT',
    headers: {
      ...headers,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
}

/**
 * Run OCR on all items in the import folder without OCR metadata
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @returns {Promise<Response>}
 */
export const ocrAll = async (apiBaseUrl, headers) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/action/ocrall`, {
    method: 'PUT',
    headers
  })
}

// ============================================================================
// Folder Actions
// ============================================================================

/**
 * Perform an action on a folder of items
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {string} folderId - Folder ID
 * @param {string} action - Action name
 * @returns {Promise<Response>}
 */
export const folderAction = async (apiBaseUrl, headers, folderId, action) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/folder/${folderId}/action/${action}`, {
    method: 'PUT',
    headers
  })
}

/**
 * Refile items in a folder with a specific token ID
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {string} folderId - Folder ID
 * @param {string} tokenId - Token ID
 * @returns {Promise<Response>}
 */
export const folderRefile = async (apiBaseUrl, headers, folderId, tokenId) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/folder/${folderId}/action/refile/${tokenId}`, {
    method: 'POST',
    headers
  })
}

/**
 * Get list of all items in a folder with review/redaction info
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {string} folderId - Folder ID
 * @returns {Promise<Response>}
 */
export const getFolderItemList = async (apiBaseUrl, headers, folderId) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/folder/${folderId}/item_list`, {
    method: 'GET',
    headers
  })
}

/**
 * Get the list of known and allowed image names for refiling
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {string} folderId - Folder ID
 * @returns {Promise<Response>}
 */
export const getFolderRefileList = async (apiBaseUrl, headers, folderId) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/folder/${folderId}/refileList`, {
    method: 'GET',
    headers
  })
}

// ============================================================================
// Item Actions
// ============================================================================

/**
 * Perform an action on an item
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {string} itemId - Item ID
 * @param {string} action - Action name
 * @returns {Promise<Response>}
 */
export const itemAction = async (apiBaseUrl, headers, itemId, action) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/item/${itemId}/action/${action}`, {
    method: 'PUT',
    headers
  })
}

/**
 * Refile an item
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {string} itemId - Item ID
 * @returns {Promise<Response>}
 */
export const itemRefile = async (apiBaseUrl, headers, itemId) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/item/${itemId}/action/refile`, {
    method: 'PUT',
    headers
  })
}

/**
 * Refile an item with a specific token ID
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {string} itemId - Item ID
 * @param {string} tokenId - Token ID
 * @returns {Promise<Response>}
 */
export const itemRefileWithToken = async (apiBaseUrl, headers, itemId, tokenId) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/item/${itemId}/action/refile/${tokenId}`, {
    method: 'POST',
    headers
  })
}

/**
 * Set the redactList meta value on an item
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {string} itemId - Item ID
 * @param {object} redactList - Redact list data
 * @returns {Promise<Response>}
 */
export const setItemRedactList = async (apiBaseUrl, headers, itemId, redactList) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/item/${itemId}/redactList`, {
    method: 'PUT',
    headers: {
      ...headers,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(redactList)
  })
}

/**
 * Get the list of known and allowed image names for refiling
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {string} itemId - Item ID
 * @returns {Promise<Response>}
 */
export const getItemRefileList = async (apiBaseUrl, headers, itemId) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/item/${itemId}/refileList`, {
    method: 'GET',
    headers
  })
}

/**
 * Get the status of a tracked item
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {string} itemId - Item ID
 * @returns {Promise<Response>}
 */
export const getItemStatus = async (apiBaseUrl, headers, itemId) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/item/${itemId}/status`, {
    method: 'GET',
    headers
  })
}

// ============================================================================
// Matching
// ============================================================================

/**
 * Pass a set of values to the Matching API
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {object} matchingData - Data to send to matching API
 * @returns {Promise<Response>}
 */
export const matching = async (apiBaseUrl, headers, matchingData) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/matching`, {
    method: 'POST',
    headers: {
      ...headers,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(matchingData)
  })
}

/**
 * Simulate the SEER*DMS Matching API for testing
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {object} matchingData - Data to send to matching API
 * @returns {Promise<Response>}
 */
export const matchingWsi = async (apiBaseUrl, headers, matchingData) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/matching/wsi`, {
    method: 'POST',
    headers: {
      ...headers,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(matchingData)
  })
}

// ============================================================================
// Status and Information
// ============================================================================

/**
 * Get the IDs of the next two folders with unprocessed items and the finished folder ID
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @returns {Promise<Response>}
 */
export const getNextUnprocessedFolders = async (apiBaseUrl, headers) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/next_unprocessed_folders`, {
    method: 'GET',
    headers
  })
}

/**
 * Get the ID of the next unprocessed item
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @returns {Promise<Response>}
 */
export const getNextUnprocessedItem = async (apiBaseUrl, headers) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/next_unprocessed_item`, {
    method: 'GET',
    headers
  })
}

/**
 * Check if a folder is a project folder
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {string} folderId - Folder ID
 * @returns {Promise<Response>}
 */
export const isProjectFolder = async (apiBaseUrl, headers, folderId) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/project_folder/${folderId}`, {
    method: 'GET',
    headers
  })
}

/**
 * Get total subtree folder and item counts of a resource by ID
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @param {string} resourceId - Resource ID
 * @returns {Promise<Response>}
 */
export const getResourceSubtreeCount = async (apiBaseUrl, headers, resourceId) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/resource/${resourceId}/subtreeCount`, {
    method: 'GET',
    headers
  })
}

/**
 * Get the current import schema
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @returns {Promise<Response>}
 */
export const getSchema = async (apiBaseUrl, headers) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/schema`, {
    method: 'GET',
    headers
  })
}

/**
 * Get settings that affect the UI
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @returns {Promise<Response>}
 */
export const getSettings = async (apiBaseUrl, headers) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/settings`, {
    method: 'GET',
    headers
  })
}

/**
 * Get the status of all tracked items in wsi_deid folders
 * @param {string} apiBaseUrl - Base API URL
 * @param {object} headers - Authentication headers
 * @returns {Promise<Response>}
 */
export const getStatus = async (apiBaseUrl, headers) => {
  const baseUrl = getWsiDeIdBaseUrl(apiBaseUrl)
  return fetch(`${baseUrl}/status`, {
    method: 'GET',
    headers
  })
}

