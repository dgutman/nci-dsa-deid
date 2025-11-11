/**
 * WSI DeID Utility Functions
 * 
 * Helper functions for working with WSI DeID collections and resources
 */

/**
 * Find the WSI DeID collection by name
 * @param {string} apiBaseUrl - The base DSA API URL
 * @param {object} headers - Authentication headers
 * @param {string} collectionName - Name of the collection to find (default: "WSI DeID")
 * @returns {Promise<object|null>} The collection object or null if not found
 */
export const findWSIDeIDCollection = async (apiBaseUrl, headers, collectionName = 'WSI DeID') => {
  try {
    const encodedName = encodeURIComponent(collectionName)
    const response = await fetch(
      `${apiBaseUrl}/collection?text=${encodedName}&limit=50&offset=0&sort=name&sortdir=1`,
      { headers }
    )
    
    if (!response.ok) {
      throw new Error(`Failed to search collections: ${response.statusText}`)
    }
    
    const data = await response.json()
    
    // Find exact match (case-insensitive)
    const collection = Array.isArray(data) 
      ? data.find(col => col.name && col.name.toLowerCase() === collectionName.toLowerCase())
      : null
    
    return collection || null
  } catch (error) {
    console.error('Error finding WSI DeID collection:', error)
    return null
  }
}

/**
 * Get all items from a resource (collection or folder) with pagination
 * @param {string} apiBaseUrl - The base DSA API URL
 * @param {object} headers - Authentication headers
 * @param {string} resourceId - The resource ID (collection or folder)
 * @param {object} options - Options for fetching items
 * @param {number} options.limit - Items per page (default: 100)
 * @param {number} options.maxItems - Maximum total items to fetch (default: null for all)
 * @param {function} options.onProgress - Optional callback for progress updates
 * @param {string} options.resourceType - Type of resource: 'collection' or 'folder' (default: 'folder')
 * @returns {Promise<Array>} Array of all items
 */
export const getAllResourceItems = async (
  apiBaseUrl,
  headers,
  resourceId,
  options = {}
) => {
  const {
    limit = 100,
    maxItems = null,
    onProgress = null,
    resourceType = 'folder'
  } = options

  const allItems = []
  let offset = 0
  let hasMore = true

  try {
    while (hasMore) {
      // Type parameter is required for both collections and folders
      const response = await fetch(
        `${apiBaseUrl}/resource/${resourceId}/items?limit=${limit}&offset=${offset}&type=${resourceType}`,
        { headers }
      )
      
      if (!response.ok) {
        throw new Error(`Failed to fetch items: ${response.statusText}`)
      }
      
      const data = await response.json()
      
      // Handle both array and paginated response formats
      let items = []
      let total = null
      
      if (Array.isArray(data)) {
        items = data
        hasMore = items.length === limit
      } else if (data.items) {
        items = data.items
        total = data.total || null
        hasMore = items.length === limit && (maxItems === null || allItems.length + items.length < maxItems)
      } else {
        // Single item or unexpected format
        items = data.item ? [data.item] : []
        hasMore = false
      }
      
      allItems.push(...items)
      
      // Call progress callback if provided
      if (onProgress) {
        onProgress({
          fetched: allItems.length,
          total: total,
          currentPage: items.length
        })
      }
      
      // Check if we've reached max items
      if (maxItems !== null && allItems.length >= maxItems) {
        hasMore = false
        // Trim to maxItems if needed
        if (allItems.length > maxItems) {
          allItems.splice(maxItems)
        }
      } else if (total !== null && allItems.length >= total) {
        hasMore = false
      } else if (items.length < limit) {
        hasMore = false
      } else {
        offset += limit
      }
    }
    
    return allItems
  } catch (error) {
    console.error('Error fetching resource items:', error)
    throw error
  }
}

/**
 * Get all items in the WSI DeID collection
 * @param {string} apiBaseUrl - The base DSA API URL
 * @param {object} headers - Authentication headers
 * @param {object} options - Options for fetching items
 * @returns {Promise<Array>} Array of all items in the WSI DeID collection
 */
export const getAllWSIDeIDItems = async (apiBaseUrl, headers, options = {}) => {
  // First, find the WSI DeID collection
  const collection = await findWSIDeIDCollection(apiBaseUrl, headers)
  
  if (!collection) {
    throw new Error('WSI DeID collection not found')
  }
  
  // Then get all items from that collection (pass resourceType='collection')
  return getAllResourceItems(apiBaseUrl, headers, collection._id, {
    ...options,
    resourceType: 'collection'
  })
}

/**
 * Get paginated items from a resource (single page)
 * @param {string} apiBaseUrl - The base DSA API URL
 * @param {object} headers - Authentication headers
 * @param {string} resourceId - The resource ID
 * @param {number} limit - Items per page (default: 100)
 * @param {number} offset - Offset for pagination (default: 0)
 * @param {string} resourceType - Type of resource: 'collection' or 'folder' (default: 'folder')
 * @returns {Promise<object>} Object with items, total, and pagination info
 */
export const getResourceItemsPage = async (
  apiBaseUrl,
  headers,
  resourceId,
  limit = 100,
  offset = 0,
  resourceType = 'folder'
) => {
  try {
    // Type parameter is required for both collections and folders
    const response = await fetch(
      `${apiBaseUrl}/resource/${resourceId}/items?limit=${limit}&offset=${offset}&type=${resourceType}`,
      { headers }
    )
    
    if (!response.ok) {
      throw new Error(`Failed to fetch items: ${response.statusText}`)
    }
    
    const data = await response.json()
    
    // Handle both array and paginated response formats
    if (Array.isArray(data)) {
      return {
        items: data,
        total: data.length,
        limit,
        offset,
        hasMore: data.length === limit
      }
    } else if (data.items) {
      return {
        items: data.items,
        total: data.total || data.items.length,
        limit,
        offset,
        hasMore: data.items.length === limit && (data.total === undefined || offset + data.items.length < data.total)
      }
    } else {
      return {
        items: data.item ? [data.item] : [],
        total: 1,
        limit,
        offset,
        hasMore: false
      }
    }
  } catch (error) {
    console.error('Error fetching resource items page:', error)
    throw error
  }
}

