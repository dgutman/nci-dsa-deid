/**
 * Check if a file with the given OutputFileName already exists in the DSA workflow folders.
 * This prevents duplicate submissions and helps identify files already in the workflow.
 * 
 * @param {string} outputFileName - The output filename to check for
 * @param {string} apiBaseUrl - Base URL for DSA API
 * @param {object} apiHeaders - Headers for API requests (must include auth)
 * @returns {Promise<{exists: boolean, path: string|null, status: string|null}>}
 */
export async function checkForExistingFile(outputFileName, apiBaseUrl, apiHeaders) {
  if (!outputFileName) {
    return { exists: false, path: null, status: null }
  }

  // Workflow folders to check
  const workflowFolders = [
    '/collection/WSI DeID/Approved',
    '/collection/WSI DeID/Redacted',
    '/collection/WSI DeID/AvailableToProcess'
  ]

  try {
    // First check by exact filename match
    const searchUrl = `${apiBaseUrl}/resource/search?q=${encodeURIComponent(outputFileName)}&mode=prefix&limit=100&types=["item"]`
    const searchResponse = await fetch(searchUrl, { headers: apiHeaders })

    if (searchResponse.ok) {
      const searchResults = await searchResponse.json()
      const items = searchResults?.item || []

      // Check each item to see if it's in a workflow folder
      for (const item of items) {
        try {
          const pathResponse = await fetch(
            `${apiBaseUrl}/resource/${item._id}/path?type=item`,
            { headers: apiHeaders }
          )

          if (pathResponse.ok) {
            let path = await pathResponse.text()
            
            // Parse JSON-encoded path if needed
            try {
              path = JSON.parse(path)
            } catch (e) {
              // Not JSON, use as-is
            }
            
            // Trim and remove quotes
            if (path) {
              path = path.trim()
              if ((path.startsWith('"') && path.endsWith('"')) || 
                  (path.startsWith("'") && path.endsWith("'"))) {
                path = path.slice(1, -1)
              }
            }

            // Check if path is in any workflow folder
            for (const folder of workflowFolders) {
              if (path && path.startsWith(folder)) {
                // Determine status from folder
                let status = null
                if (path.startsWith('/collection/WSI DeID/Approved')) {
                  status = 'Approved'
                } else if (path.startsWith('/collection/WSI DeID/Redacted')) {
                  status = 'Redacted'
                } else if (path.startsWith('/collection/WSI DeID/AvailableToProcess')) {
                  status = 'AvailableToProcess'
                }

                return {
                  exists: true,
                  path: path,
                  status: status
                }
              }
            }
          }
        } catch (e) {
          // Continue checking other items if path fetch fails
          console.warn(`Failed to get path for item ${item._id}:`, e)
        }
      }
    }

    // Also check for files with (1), (2), etc. suffixes that might be duplicates
    const lastDotIndex = outputFileName.lastIndexOf('.')
    const baseName = lastDotIndex > 0 
      ? outputFileName.substring(0, lastDotIndex)
      : outputFileName
    const extension = lastDotIndex > 0 
      ? outputFileName.substring(lastDotIndex)
      : ''

    // Check for potential duplicates with number suffixes (1) through (9)
    for (let i = 1; i < 10; i++) {
      const potentialDuplicate = `${baseName} (${i})${extension}`
      const duplicateSearchUrl = `${apiBaseUrl}/resource/search?q=${encodeURIComponent(potentialDuplicate)}&mode=prefix&limit=100&types=["item"]`
      
      try {
        const duplicateSearchResponse = await fetch(duplicateSearchUrl, { headers: apiHeaders })
        
        if (duplicateSearchResponse.ok) {
          const duplicateResults = await duplicateSearchResponse.json()
          const duplicateItems = duplicateResults?.item || []

          for (const item of duplicateItems) {
            try {
              const pathResponse = await fetch(
                `${apiBaseUrl}/resource/${item._id}/path?type=item`,
                { headers: apiHeaders }
              )

              if (pathResponse.ok) {
                let path = await pathResponse.text()
                
                try {
                  path = JSON.parse(path)
                } catch (e) {
                  // Not JSON, use as-is
                }
                
                if (path) {
                  path = path.trim()
                  if ((path.startsWith('"') && path.endsWith('"')) || 
                      (path.startsWith("'") && path.endsWith("'"))) {
                    path = path.slice(1, -1)
                  }
                }

                for (const folder of workflowFolders) {
                  if (path && path.startsWith(folder)) {
                    let status = null
                    if (path.startsWith('/collection/WSI DeID/Approved')) {
                      status = 'Approved'
                    } else if (path.startsWith('/collection/WSI DeID/Redacted')) {
                      status = 'Redacted'
                    } else if (path.startsWith('/collection/WSI DeID/AvailableToProcess')) {
                      status = 'AvailableToProcess'
                    }

                    return {
                      exists: true,
                      path: path,
                      status: status,
                      isDuplicate: true,
                      duplicateName: potentialDuplicate
                    }
                  }
                }
              }
            } catch (e) {
              // Continue checking
            }
          }
        }
      } catch (e) {
        // Continue to next number
      }
    }

    return { exists: false, path: null, status: null }
  } catch (error) {
    console.error('Error checking for existing file:', error)
    // Return false on error to allow processing to continue
    return { exists: false, path: null, status: null, error: error.message }
  }
}

