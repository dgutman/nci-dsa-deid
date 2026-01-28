import { useState, useEffect, useRef, useMemo } from 'react'
import { createPortal } from 'react-dom'
import { FolderBrowser, useDsaAuth } from 'bdsa-react-components'
import { AgGridReact } from 'ag-grid-react'
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import { themeQuartz } from 'ag-grid-community'
import Papa from 'papaparse'
import config from '../config'
import { checkForExistingFile } from '../utils/duplicateDetection'

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule])

// Columns to copy from metadata when matched
const COLS_FOR_COPY = [
  'SampleID',
  'REPOSITORY',
  'STUDY',
  'PROJECT',
  'CASE',
  'BLOCK',
  'ASSAY',
  'INDEX',
  'ImageID',
  'OutputFileName'
]

// Match items with metadata
const matchItemsWithMetadata = (itemsList, metadataList) => {
  if (!metadataList || metadataList.length === 0) {
    return itemsList.map(item => ({
      ...item,
      match_result: 'No Match'
    }))
  }

  // Create metadata mapping by InputFileName
  const metadataMapping = {}
  metadataList.forEach(meta => {
    if (meta.InputFileName) {
      metadataMapping[meta.InputFileName] = meta
    }
  })

  // Process each item
  return itemsList.map(item => {
    const itemCopy = { ...item }
    itemCopy.InputFileName = item.name // Set InputFileName to item name

    if (item.name in metadataMapping) {
      // Match found
      itemCopy.match_result = 'Match'
      const matchedMetadata = metadataMapping[item.name]

      // Copy all COLS_FOR_COPY fields from metadata
      COLS_FOR_COPY.forEach(col => {
        if (col in matchedMetadata) {
          itemCopy[col] = matchedMetadata[col]
        }
      })
    } else {
      // No match
      itemCopy.match_result = 'No Match'
      // Fill with empty values
      COLS_FOR_COPY.forEach(col => {
        itemCopy[col] = ' '
      })
    }

    return itemCopy
  })
}

function SlidesForDeID() {
  // Load selected folder from localStorage on mount
  const [selectedResource, setSelectedResource] = useState(() => {
    try {
      const stored = localStorage.getItem('deid_selected_folder')
      return stored ? JSON.parse(stored) : null
    } catch (error) {
      console.error('Error loading selected folder from localStorage:', error)
      return null
    }
  })
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const { authStatus, getAuthHeaders, getApiUrl } = useDsaAuth()
  const lastFetchedFolderId = useRef(null)
  const originalItemsRef = useRef([])

  // Fetch items when a folder is selected
  useEffect(() => {
    const folderId = selectedResource?._modelType === 'folder' ? selectedResource._id : null

    if (!folderId || !authStatus.isAuthenticated) {
      setItems([])
      lastFetchedFolderId.current = null
      return
    }

    // Prevent fetching the same folder multiple times
    if (lastFetchedFolderId.current === folderId) {
      return
    }

    const fetchItems = async () => {
      // Get API base URL and headers inside the effect to avoid dependency issues
      const apiBaseUrl = authStatus.isConfigured
        ? getApiUrl('/api/v1')
        : config.apiBaseUrl
      const apiHeaders = getAuthHeaders()

      setLoading(true)
      lastFetchedFolderId.current = folderId

      try {
        const response = await fetch(
          `${apiBaseUrl}/item?folderId=${folderId}&limit=1000`,
          { headers: apiHeaders }
        )

        if (!response.ok) {
          throw new Error(`Failed to fetch items: ${response.statusText}`)
        }

        const data = await response.json()
        // Fetched items from folder

        // Handle both array and paginated response
        const itemsList = Array.isArray(data) ? data : (data.items || [])

        // Add match_result field (will be determined later when metadata is available)
        const itemsWithMatchStatus = itemsList.map(item => ({
          ...item,
          match_result: 'No Match' // Default, will be updated when metadata is matched
        }))
        // Setting items with match status

        // Store original items before matching
        originalItemsRef.current = itemsWithMatchStatus.map(item => ({ ...item }))

        // Check if metadata exists and match items
        try {
          const storedMetadata = localStorage.getItem('deid_metadata')
          if (storedMetadata) {
            const metadata = JSON.parse(storedMetadata)
            const matchedItems = matchItemsWithMetadata(itemsWithMatchStatus, metadata)
            setItems(matchedItems)
            localStorage.setItem('deid_selected_folder_items', JSON.stringify(matchedItems))
          } else {
            setItems(itemsWithMatchStatus)
            localStorage.setItem('deid_selected_folder_items', JSON.stringify(itemsWithMatchStatus))
          }
        } catch (error) {
          console.error('Error matching on fetch:', error)
          setItems(itemsWithMatchStatus)
          localStorage.setItem('deid_selected_folder_items', JSON.stringify(itemsWithMatchStatus))
        }

        localStorage.setItem('deid_selected_folder_id', folderId)
      } catch (error) {
        console.error('Error fetching items:', error)
        setItems([])
        lastFetchedFolderId.current = null
      } finally {
        setLoading(false)
      }
    }

    fetchItems()
  }, [selectedResource?._id, authStatus.isAuthenticated])

  const handleResourceSelect = (resource) => {
    // Resource selected
    setSelectedResource(resource)
    // Persist selected folder to localStorage
    try {
      localStorage.setItem('deid_selected_folder', JSON.stringify(resource))
    } catch (error) {
      console.error('Error saving selected folder to localStorage:', error)
    }
  }

  const handleDownloadTemplate = () => {
    // Filter for files with "No Match" status
    const noMatchFiles = items.filter(item => item.match_result === 'No Match')

    if (noMatchFiles.length === 0) {
      alert('No unmatched files to generate template for.')
      return
    }

    // Create template data
    const templateData = noMatchFiles.map((item, index) => {
      const filename = item.name || ''
      // Generate a sample ID from filename (you can customize this logic)
      const sampleId = filename.includes('-')
        ? filename.split('-')[0]
        : `SAMPLE_${String(index + 1).padStart(3, '0')}`

      return {
        InputFileName: filename,
        SampleID: sampleId,
        REPOSITORY: 'DCEG',
        STUDY: 'MR-0600',
        PROJECT: 'HP0600-001',
        CASE: 'TestProject',
        BLOCK: `BR${String(index + 1).padStart(4, '0')}`,
        ASSAY: 'H&E',
        INDEX: String(index + 1),
        ImageID: 'SA',
        OutputFileName: `${sampleId}.S${index + 1}.DEID.svs`
      }
    })

    // Convert to CSV using PapaParse
    const csv = Papa.unparse(templateData)

    // Create download link
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', 'metadata_template.csv')
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }


  // Update original items when new items are fetched
  useEffect(() => {
    if (items.length > 0 && items[0]._id && !items[0].InputFileName) {
      // These are fresh items from the API, store them as originals
      originalItemsRef.current = items.map(item => ({ ...item }))
    }
  }, [selectedResource?._id]) // Only when folder changes

  // Match items with metadata when items or metadata change
  const matchItemsWithCurrentMetadata = () => {
    try {
      const storedMetadata = localStorage.getItem('deid_metadata')
      const originalItems = originalItemsRef.current.length > 0
        ? originalItemsRef.current
        : items.filter(item => !item.InputFileName || item.match_result === 'No Match')

      if (storedMetadata && originalItems.length > 0) {
        const metadata = JSON.parse(storedMetadata)
        const matchedItems = matchItemsWithMetadata(originalItems, metadata)
        setItems(matchedItems)
        localStorage.setItem('deid_selected_folder_items', JSON.stringify(matchedItems))
      } else if (originalItems.length > 0 && items.length > 0) {
        // No metadata, ensure items are marked as No Match
        const hasMatches = items.some(item => item.match_result === 'Match')
        if (hasMatches) {
          const unmatchedItems = originalItems.map(item => ({
            ...item,
            match_result: 'No Match'
          }))
          setItems(unmatchedItems)
        }
      }
    } catch (error) {
      console.error('Error matching items with metadata:', error)
    }
  }

  // Listen for metadata updates via storage events (from other tabs/components)
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'deid_metadata' && items.length > 0) {
        matchItemsWithCurrentMetadata()
      }
    }

    // Listen for storage events (fires when localStorage changes from other tabs/windows)
    window.addEventListener('storage', handleStorageChange)

    // Also listen for custom event for same-window updates
    const handleMetadataUpdate = () => {
      if (items.length > 0) {
        matchItemsWithCurrentMetadata()
      }
    }
    window.addEventListener('deid_metadata_updated', handleMetadataUpdate)

    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('deid_metadata_updated', handleMetadataUpdate)
    }
  }, [items.length]) // Re-setup listeners when items change

  // Check if download button should be enabled
  const hasUnmatchedFiles = items.some(item => item.match_result === 'No Match')

  // Check if there are matched items ready to stage
  const matchedItems = items.filter(item => item.match_result === 'Match' && item.OutputFileName)
  const hasMatchedFiles = matchedItems.length > 0
  const [staging, setStaging] = useState(false)

  // Generate metadata from current folder items (DEV function)
  const handleDevGenerateMetadata = () => {
    if (items.length === 0) {
      alert('No items in selected folder. Please select a folder with items first.')
      return
    }

    // Generate metadata from folder items (same logic as download template)
    const today = new Date()
    const batchId = `Batch-${today.getFullYear()}${String(today.getMonth() + 1).padStart(2, '0')}${String(today.getDate()).padStart(2, '0')}`

    const generatedMetadata = items.map((item, index) => {
      const filename = item.name || ''

      // Generate sample ID from filename (similar to download template logic)
      let sampleId = filename.includes('-')
        ? filename.split('-')[0]
        : `SAMPLE_${String(index + 1).padStart(3, '0')}`

      // If filename starts with TCGA, use TCGA pattern
      if (filename.startsWith('TCGA-')) {
        const parts = filename.split('-')
        if (parts.length >= 2) {
          sampleId = `TCGA-${parts[1]}`
        }
      }

      // Generate output filename
      let outputFileName = filename
      if (filename.endsWith('.svs')) {
        outputFileName = `${sampleId}.S${index + 1}.DEID.svs`
      } else {
        outputFileName = `${sampleId}.S${index + 1}.DEID.svs`
      }

      return {
        InputFileName: filename,
        SampleID: sampleId || batchId,
        REPOSITORY: 'DCEG',
        STUDY: 'MR-0600',
        PROJECT: 'HP0600-001',
        CASE: 'TestProject',
        BLOCK: `BR${String(index + 1).padStart(4, '0')}`,
        ASSAY: 'H&E',
        INDEX: String(index + 1),
        ImageID: 'SA',
        OutputFileName: outputFileName
      }
    })

    // Store metadata in localStorage so Metadata page can access it
    localStorage.setItem('deid_metadata', JSON.stringify(generatedMetadata))
    localStorage.setItem('deid_metadata_filename', `Generated from ${selectedResource?.name || 'folder'} (${items.length} items) [DEV]`)

    // Match items immediately with the generated metadata
    const matchedItems = matchItemsWithMetadata(originalItemsRef.current.length > 0 ? originalItemsRef.current : items, generatedMetadata)
    setItems(matchedItems)
    localStorage.setItem('deid_selected_folder_items', JSON.stringify(matchedItems))

    // Dispatch custom event to notify other components
    window.dispatchEvent(new Event('deid_metadata_updated'))
  }

  // Stage matched files for DEID
  const handleStageFiles = async () => {
    if (matchedItems.length === 0) {
      alert('No matched files to stage.')
      return
    }

    setStaging(true)

    try {
      const apiBaseUrl = authStatus.isConfigured
        ? getApiUrl('/api/v1')
        : config.apiBaseUrl
      const apiHeaders = getAuthHeaders()

      // Find the Unfiled folder
      const unfiledPath = '/collection/WSI DeID/Unfiled'
      const unfiledResponse = await fetch(
        `${apiBaseUrl}/resource/lookup?path=${encodeURIComponent(unfiledPath)}`,
        { headers: apiHeaders }
      )

      if (!unfiledResponse.ok) {
        throw new Error('Failed to find Unfiled folder')
      }

      const unfiledFolder = await unfiledResponse.json()
      const unfiledFolderId = unfiledFolder._id

      let stagedCount = 0
      let skippedCount = 0
      let duplicateCount = 0
      const errors = []
      const duplicateWarnings = []

      // Get list of items already in Unfiled folder (we'll check if we can reuse them)
      const unfiledItemsResponse = await fetch(
        `${apiBaseUrl}/item?folderId=${unfiledFolderId}&limit=1000`,
        { headers: apiHeaders }
      )

      let unfiledItems = []
      if (unfiledItemsResponse.ok) {
        const unfiledItemsData = await unfiledItemsResponse.json()
        unfiledItems = Array.isArray(unfiledItemsData) ? unfiledItemsData : (unfiledItemsData.items || [])
      }

      // Process each matched item
      for (const item of matchedItems) {
        try {
          // Check if file already exists in workflow folders (Approved, Redacted, AvailableToProcess)
          // If it's already in AvailableToProcess or beyond, skip it
          const existingCheck = await checkForExistingFile(
            item.OutputFileName,
            apiBaseUrl,
            apiHeaders
          )

          if (existingCheck.exists) {
            duplicateCount++
            duplicateWarnings.push(
              `${item.name}: OutputFileName "${item.OutputFileName}" already exists in ${existingCheck.status || 'workflow'} folder`
            )
            continue // Skip this file - it's already in the workflow
          }

          // Check if file already exists in Unfiled by output filename
          // If it exists, we can reuse it and refile it (don't skip it!)
          const existingUnfiled = unfiledItems.find(i => {
            const meta = i.meta?.deidUpload
            return meta?.OutputFileName === item.OutputFileName
          })

          let itemToRefile = null

          if (existingUnfiled) {
            // File already exists in Unfiled - use it directly for refiling
            // No need to copy again, just refile the existing one
            // File already exists in Unfiled, will refile existing item
            itemToRefile = existingUnfiled
          } else {
            // File doesn't exist in Unfiled - copy it there first
            const copyResponse = await fetch(
              `${apiBaseUrl}/item/${item._id}/copy?folderId=${unfiledFolderId}`,
              {
                method: 'POST',
                headers: apiHeaders
              }
            )

            if (!copyResponse.ok) {
              throw new Error(`Failed to copy item ${item.name}`)
            }

            itemToRefile = await copyResponse.json()
          }

          // Add/update metadata to the item (whether it's newly copied or existing in Unfiled)
          const metadataToAdd = {
            deidUpload: {
              InputFileName: item.InputFileName || item.name,
              SampleID: item.SampleID,
              REPOSITORY: item.REPOSITORY,
              STUDY: item.STUDY,
              PROJECT: item.PROJECT,
              CASE: item.CASE,
              BLOCK: item.BLOCK,
              ASSAY: item.ASSAY,
              INDEX: item.INDEX,
              ImageID: item.ImageID,
              OutputFileName: item.OutputFileName
            }
          }

          const metaResponse = await fetch(
            `${apiBaseUrl}/item/${itemToRefile._id}/metadata`,
            {
              method: 'PUT',
              headers: {
                ...apiHeaders,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify(metadataToAdd)
            }
          )

          if (!metaResponse.ok) {
            throw new Error(`Failed to add metadata to ${item.name}`)
          }

          // Refile the item using WSI DeID API
          // The refile API should move the file from Unfiled to AvailableToProcess folder
          const imageName = item.OutputFileName.replace('.svs', '')
          const refileUrl = `${apiBaseUrl}/wsi_deid/item/${itemToRefile._id}/action/refile?imageId=${encodeURIComponent(imageName)}&tokenId=${encodeURIComponent(item.SampleID)}`

          // Attempting to refile item to AvailableToProcess folder

          const refileResponse = await fetch(refileUrl, {
            method: 'PUT',
            headers: apiHeaders
          })

          if (refileResponse.ok) {
            const refiledItem = await refileResponse.json()
            // Successfully refiled item

            // After refiling, add barcode metadata (keys used for barcode encoding)
            // The Dash version only adds barcode keys after refile, not the full metadata
            const keysForBarcode = ['ASSAY', 'BLOCK', 'CASE', 'INDEX', 'PROJECT', 'REPOSITORY', 'STUDY']
            const metaForBarcode = {}

            keysForBarcode.forEach(key => {
              if (item[key] !== undefined && item[key] !== null && item[key] !== ' ') {
                metaForBarcode[key] = item[key]
              }
            })

            // Also preserve InputFileName and OutputFileName
            if (item.InputFileName) {
              metaForBarcode.InputFileName = item.InputFileName
            }
            if (item.OutputFileName) {
              metaForBarcode.OutputFileName = item.OutputFileName
            }

            // Add the barcode metadata to the refiled item
            const refiledMetaResponse = await fetch(
              `${apiBaseUrl}/item/${refiledItem._id}/metadata`,
              {
                method: 'PUT',
                headers: {
                  ...apiHeaders,
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                  deidUpload: metaForBarcode
                })
              }
            )

            if (!refiledMetaResponse.ok) {
              const errorText = await refiledMetaResponse.text()
              console.warn(`Failed to add barcode metadata to refiled item ${item.name}:`, errorText)
            } else {
              // Successfully added barcode metadata
            }
          } else {
            // Refile failed - check if it's because the file already exists
            const errorText = await refileResponse.text()
            const errorStatus = refileResponse.status
            let errorData = null

            try {
              errorData = JSON.parse(errorText)
            } catch (e) {
              // Not JSON, use as-is
            }

            // If the error is "already exists", check if the file is actually in AvailableToProcess
            if (errorStatus === 400 && errorData?.message?.includes('already exists')) {
              // Refile returned "already exists", checking if file is in workflow...

              // Check if the file already exists in AvailableToProcess by searching in the tokenId subfolder
              // The refile API checks for files by imageId (without extension) in the tokenId subfolder
              const imageName = item.OutputFileName.replace('.svs', '')
              const availableToProcessPath = `/collection/WSI DeID/AvailableToProcess/${item.SampleID}`

              try {
                // Look up the tokenId subfolder
                const tokenFolderResponse = await fetch(
                  `${apiBaseUrl}/resource/lookup?path=${encodeURIComponent(availableToProcessPath)}`,
                  { headers: apiHeaders }
                )

                if (tokenFolderResponse.ok) {
                  const tokenFolder = await tokenFolderResponse.json()

                  // Search for items in that folder with the imageId name
                  const itemsResponse = await fetch(
                    `${apiBaseUrl}/item?folderId=${tokenFolder._id}&limit=1000`,
                    { headers: apiHeaders }
                  )

                  if (itemsResponse.ok) {
                    const itemsData = await itemsResponse.json()
                    const itemsList = Array.isArray(itemsData) ? itemsData : (itemsData.items || [])

                    // Check if any item matches the imageId (with or without extension)
                    const matchingItem = itemsList.find(i => {
                      const itemName = i.name || ''
                      // Match if the item name starts with the imageId (handles extensions)
                      return itemName.startsWith(imageName + '.') || itemName === imageName
                    })

                    if (matchingItem) {
                      // File is already in AvailableToProcess - this is actually a success!
                      // File already exists in AvailableToProcess, skipping refile
                      stagedCount++
                      continue // Skip to next item
                    }
                  }
                }
              } catch (e) {
                console.warn(`Error checking for existing file in ${availableToProcessPath}:`, e)
              }

              // Also check using the general checkForExistingFile function
              // This checks Approved, Redacted, and AvailableToProcess folders
              const existingCheck = await checkForExistingFile(
                item.OutputFileName,
                apiBaseUrl,
                apiHeaders
              )

              if (existingCheck.exists) {
                // File exists in one of the workflow folders - this is actually a success!
                // It might be in AvailableToProcess, Approved, or Redacted
                // File already exists in workflow folder, skipping refile
                stagedCount++
                continue // Skip to next item
              } else {
                // File doesn't exist in any workflow folder, but refile says it exists
                // This could mean:
                // 1. The file was refiled before but then deleted/moved
                // 2. There's a race condition
                // 3. The check is looking in a different location
                // For now, log a warning but don't fail - the file might have been processed already
                console.warn(`Refile says file exists but couldn't find it in any workflow folder. The file may have been processed and moved elsewhere, or there may be a naming mismatch.`)
                // Don't throw an error - just skip this file
                skippedCount++
                continue
              }
            } else {
              // Some other error
              console.error(`Refile failed for ${item.name}:`, {
                status: errorStatus,
                statusText: refileResponse.statusText,
                error: errorText
              })
              throw new Error(`Refile failed (${errorStatus}): ${errorText || refileResponse.statusText}. File is in Unfiled folder but not moved to AvailableToProcess.`)
            }
          }

          stagedCount++
        } catch (error) {
          console.error(`Error staging ${item.name}:`, error)
          errors.push(`${item.name}: ${error.message}`)
        }
      }

      // Show results
      let message = `Staged ${stagedCount} file(s) for DEID.`
      if (duplicateCount > 0) {
        message += `\n\n${duplicateCount} file(s) skipped - already exist in workflow:\n${duplicateWarnings.slice(0, 5).join('\n')}`
        if (duplicateWarnings.length > 5) {
          message += `\n... and ${duplicateWarnings.length - 5} more`
        }
      }
      // Note: We no longer skip files in Unfiled - we refile them to AvailableToProcess
      // So skippedCount should always be 0 now
      if (errors.length > 0) {
        message += `\n${errors.length} error(s) occurred.`
        console.error('Staging errors:', errors)
      }

      alert(message)

      // Refresh items to update status
      if (selectedResource?._id) {
        lastFetchedFolderId.current = null
        // Trigger refetch by updating a dependency
        setItems([...items])
      }
    } catch (error) {
      console.error('Error staging files:', error)
      alert(`Error staging files: ${error.message}`)
    } finally {
      setStaging(false)
    }
  }

  // Format file size for display
  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  // Thumbnail cell renderer component
  const ThumbnailCellRenderer = ({ data }) => {
    const [labelSrc, setLabelSrc] = useState(null)
    const [macroSrc, setMacroSrc] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [labelMissing, setLabelMissing] = useState(false)
    const [macroMissing, setMacroMissing] = useState(false)
    const [hoveredImage, setHoveredImage] = useState(null) // 'label' or 'macro' or null
    const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 })
    const labelRef = useRef(null)
    const macroRef = useRef(null)

    useEffect(() => {
      if (!data?._id || !authStatus.isAuthenticated) {
        setLoading(false)
        return
      }

      const apiBaseUrl = authStatus.isConfigured
        ? getApiUrl('/api/v1')
        : config.apiBaseUrl
      const apiHeaders = getAuthHeaders()

      // Fetch label and macro images
      const fetchImages = async () => {
        try {
          setLoading(true)
          setLabelSrc(null)
          setMacroSrc(null)
          setLabelMissing(false)
          setMacroMissing(false)

          // Try to fetch label image
          try {
            const labelResponse = await fetch(
              `${apiBaseUrl}/item/${data._id}/tiles/images/label`,
              { headers: apiHeaders }
            )
            if (labelResponse.ok) {
              const labelBlob = await labelResponse.blob()
              // Check if the blob is actually an image (not an error page)
              if (labelBlob.type.startsWith('image/')) {
                setLabelSrc(URL.createObjectURL(labelBlob))
                setLabelMissing(false)
              } else {
                setLabelMissing(true)
              }
            } else if (labelResponse.status === 404) {
              setLabelMissing(true)
            } else {
              // Other error status - mark as missing
              setLabelMissing(true)
            }
          } catch (e) {
            // Network error or other exception - mark as missing
            setLabelMissing(true)
          }

          // Try to fetch macro image
          try {
            const macroResponse = await fetch(
              `${apiBaseUrl}/item/${data._id}/tiles/images/macro`,
              { headers: apiHeaders }
            )
            if (macroResponse.ok) {
              const macroBlob = await macroResponse.blob()
              // Check if the blob is actually an image (not an error page)
              if (macroBlob.type.startsWith('image/')) {
                setMacroSrc(URL.createObjectURL(macroBlob))
                setMacroMissing(false)
              } else {
                setMacroMissing(true)
              }
            } else if (macroResponse.status === 404) {
              setMacroMissing(true)
            } else {
              // Other error status - mark as missing
              setMacroMissing(true)
            }
          } catch (e) {
            // Network error or other exception - mark as missing
            setMacroMissing(true)
          }
        } catch (err) {
          console.error('Error fetching thumbnails:', err)
          setError(err.message)
        } finally {
          setLoading(false)
        }
      }

      fetchImages()

      // Cleanup object URLs on unmount or when data changes
      return () => {
        if (labelSrc) {
          URL.revokeObjectURL(labelSrc)
        }
        if (macroSrc) {
          URL.revokeObjectURL(macroSrc)
        }
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [data?._id, authStatus.isAuthenticated])

    if (loading) {
      return (
        <div style={{ padding: '4px', textAlign: 'center', fontSize: '0.75rem', color: '#666' }}>
          Loading...
        </div>
      )
    }

    if (error) {
      return (
        <div style={{ padding: '4px', textAlign: 'center', fontSize: '0.75rem', color: '#999' }}>
          N/A
        </div>
      )
    }

    // Show appropriate message if no images are available
    if (!loading && !labelSrc && !macroSrc && (labelMissing && macroMissing)) {
      return (
        <div style={{ padding: '4px', textAlign: 'center', fontSize: '0.75rem', color: '#999' }}>
          No images available
        </div>
      )
    }

    const updateHoverPosition = (imageType) => {
      const ref = imageType === 'label' ? labelRef : macroRef
      if (!ref.current) return

      // Get the bounding rect of the thumbnail element
      const rect = ref.current.getBoundingClientRect()
      // Position overlay above the thumbnail, centered horizontally
      const centerX = rect.left + rect.width / 2
      const topY = rect.top

      setHoverPosition({
        x: centerX,
        y: topY
      })
    }

    const handleMouseEnter = (imageType) => {
      setHoveredImage(imageType)
      // Use setTimeout to ensure ref is set
      setTimeout(() => updateHoverPosition(imageType), 0)
    }

    const handleMouseLeave = () => {
      setHoveredImage(null)
    }

    const handleMouseMove = () => {
      if (hoveredImage) {
        updateHoverPosition(hoveredImage)
      }
    }

    return (
      <>
        <div style={{
          display: 'flex',
          gap: '4px',
          padding: '4px',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          {labelSrc ? (
            <div
              ref={labelRef}
              style={{ position: 'relative' }}
              onMouseEnter={() => handleMouseEnter('label')}
              onMouseLeave={handleMouseLeave}
              onMouseMove={handleMouseMove}
            >
              <img
                src={labelSrc}
                alt="Label"
                style={{
                  width: '60px',
                  height: '60px',
                  objectFit: 'contain',
                  border: '1px solid #ddd',
                  borderRadius: '2px',
                  backgroundColor: '#f5f5f5',
                  cursor: 'pointer'
                }}
                title="Label Image - Hover to enlarge"
                onError={() => {
                  setLabelMissing(true)
                  setLabelSrc(null)
                }}
              />
              <div style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                backgroundColor: 'rgba(0,0,0,0.6)',
                color: 'white',
                fontSize: '0.6rem',
                padding: '1px 2px',
                textAlign: 'center'
              }}>
                Label
              </div>
            </div>
          ) : labelMissing ? (
            <div
              style={{
                width: '60px',
                height: '60px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid #ddd',
                borderRadius: '2px',
                backgroundColor: '#f5f5f5',
                fontSize: '0.6rem',
                color: '#999',
                textAlign: 'center',
                padding: '4px'
              }}
              title="Label image not available"
            >
              No Label
            </div>
          ) : null}
          {macroSrc ? (
            <div
              ref={macroRef}
              style={{ position: 'relative' }}
              onMouseEnter={() => handleMouseEnter('macro')}
              onMouseLeave={handleMouseLeave}
              onMouseMove={handleMouseMove}
            >
              <img
                src={macroSrc}
                alt="Macro"
                style={{
                  width: '60px',
                  height: '60px',
                  objectFit: 'contain',
                  border: '1px solid #ddd',
                  borderRadius: '2px',
                  backgroundColor: '#f5f5f5',
                  cursor: 'pointer'
                }}
                title="Macro Image - Hover to enlarge"
                onError={() => {
                  setMacroMissing(true)
                  setMacroSrc(null)
                }}
              />
              <div style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                backgroundColor: 'rgba(0,0,0,0.6)',
                color: 'white',
                fontSize: '0.6rem',
                padding: '1px 2px',
                textAlign: 'center'
              }}>
                Macro
              </div>
            </div>
          ) : macroMissing ? (
            <div
              style={{
                width: '60px',
                height: '60px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid #ddd',
                borderRadius: '2px',
                backgroundColor: '#f5f5f5',
                fontSize: '0.6rem',
                color: '#999',
                textAlign: 'center',
                padding: '4px'
              }}
              title="Macro image not available"
            >
              No Macro
            </div>
          ) : null}
        </div>
        {/* Hover overlay for enlarged image - rendered via portal */}
        {hoveredImage && (hoveredImage === 'label' ? labelSrc : macroSrc) && hoverPosition.x > 0 && hoverPosition.y > 0 && createPortal(
          <div
            style={{
              position: 'fixed',
              left: `${hoverPosition.x}px`,
              top: `${hoverPosition.y}px`,
              transform: 'translate(calc(-100% + 30px), calc(-100% - 8px))',
              zIndex: 10000,
              pointerEvents: 'none',
              maxWidth: `${Math.min(400, window.innerWidth - 40)}px`,
              maxHeight: `${Math.min(400, hoverPosition.y - 40)}px`
            }}
          >
            <div style={{
              backgroundColor: 'white',
              border: '2px solid #0066cc',
              borderRadius: '4px',
              padding: '4px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
              maxWidth: '100%',
              maxHeight: '100%'
            }}>
              <img
                src={hoveredImage === 'label' ? labelSrc : macroSrc}
                alt={hoveredImage === 'label' ? 'Label (enlarged)' : 'Macro (enlarged)'}
                style={{
                  width: 'auto',
                  height: 'auto',
                  maxWidth: '100%',
                  maxHeight: 'calc(100% - 30px)',
                  objectFit: 'contain',
                  display: 'block'
                }}
              />
              <div style={{
                backgroundColor: 'rgba(0,0,0,0.7)',
                color: 'white',
                fontSize: '0.75rem',
                padding: '2px 6px',
                textAlign: 'center',
                marginTop: '4px',
                borderRadius: '2px'
              }}>
                {hoveredImage === 'label' ? 'Label Image' : 'Macro Image'}
              </div>
            </div>
          </div>,
          document.body
        )}
      </>
    )
  }

  // AG Grid column definitions
  const columnDefs = useMemo(() => [
    {
      field: '_id',
      headerName: 'Thumbnails',
      width: 140,
      resizable: true,
      sortable: false,
      filter: false,
      pinned: 'left',
      cellRenderer: ThumbnailCellRenderer
    },
    {
      field: 'name',
      headerName: 'Filename',
      flex: 2,
      resizable: true,
      sortable: true,
      filter: true
    },
    {
      field: 'size',
      headerName: 'File Size',
      width: 150,
      resizable: true,
      sortable: true,
      filter: true,
      valueFormatter: (params) => formatFileSize(params.value)
    },
    {
      field: '_id',
      headerName: 'DSA ID',
      flex: 1,
      resizable: true,
      sortable: true,
      filter: true
    },
    {
      field: 'match_result',
      headerName: 'Matching Metadata',
      width: 180,
      resizable: true,
      sortable: true,
      filter: true,
      cellStyle: (params) => {
        if (params.value === 'No Match') {
          return { fontWeight: 'bold', color: 'red' }
        } else if (params.value === 'Match') {
          return { fontWeight: 'bold', color: 'green' }
        }
        return null
      }
    },
    {
      field: 'OutputFileName',
      headerName: 'Output File Name',
      flex: 1.5,
      resizable: true,
      sortable: true,
      filter: true,
      valueGetter: (params) => {
        // Show OutputFileName if available, otherwise show empty or placeholder
        return params.data?.OutputFileName || ''
      },
      cellStyle: (params) => {
        // Style matched items differently
        if (params.data?.match_result === 'Match' && params.value) {
          return { color: '#0066cc', fontWeight: 500 }
        }
        return null
      }
    }
  ], [])

  const defaultColDef = useMemo(() => ({
    resizable: true,
    sortable: true,
    filter: true
  }), [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '600px' }}>
      {/* Compact Toolbar */}
      {selectedResource && selectedResource._modelType === 'folder' ? (
        <div style={{
          padding: '0.5rem 1rem',
          backgroundColor: '#e8f4f8',
          borderRadius: '4px',
          border: '1px solid #b3d9e6',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '0.75rem',
          flexShrink: 0
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.9rem' }}>
            <span><strong style={{ color: '#0066cc' }}>Folder:</strong> {selectedResource.name}</span>
            {items.length > 0 && (
              <>
                <span style={{ color: '#666' }}>•</span>
                <span style={{ color: '#666' }}>{items.length} item(s)</span>
                {hasUnmatchedFiles && (
                  <>
                    <span style={{ color: '#666' }}>•</span>
                    <span style={{ color: '#dc3545', fontWeight: 500 }}>
                      {items.filter(i => i.match_result === 'No Match').length} unmatched
                    </span>
                  </>
                )}
              </>
            )}
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={handleDevGenerateMetadata}
              disabled={items.length === 0 || loading}
              style={{
                padding: '0.4rem 0.9rem',
                backgroundColor: items.length > 0 ? '#ff6b35' : '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: items.length > 0 ? 'pointer' : 'not-allowed',
                fontWeight: 500,
                fontSize: '0.85rem',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => {
                if (items.length > 0) e.target.style.backgroundColor = '#e55a2b'
              }}
              onMouseLeave={(e) => {
                if (items.length > 0) e.target.style.backgroundColor = '#ff6b35'
              }}
            >
              [DEV] Generate Metadata
            </button>
            <button
              onClick={handleDownloadTemplate}
              disabled={!hasUnmatchedFiles || loading}
              style={{
                padding: '0.4rem 0.9rem',
                backgroundColor: hasUnmatchedFiles ? '#28a745' : '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: hasUnmatchedFiles ? 'pointer' : 'not-allowed',
                fontWeight: 500,
                fontSize: '0.85rem',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => {
                if (hasUnmatchedFiles) e.target.style.backgroundColor = '#218838'
              }}
              onMouseLeave={(e) => {
                if (hasUnmatchedFiles) e.target.style.backgroundColor = '#28a745'
              }}
            >
              {loading ? 'Loading...' : 'Download Template'}
            </button>
            {hasMatchedFiles && (
              <button
                onClick={handleStageFiles}
                disabled={staging || !hasMatchedFiles}
                style={{
                  padding: '0.4rem 0.9rem',
                  backgroundColor: hasMatchedFiles && !staging ? '#0066cc' : '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: hasMatchedFiles && !staging ? 'pointer' : 'not-allowed',
                  fontWeight: 500,
                  fontSize: '0.85rem',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => {
                  if (hasMatchedFiles && !staging) e.target.style.backgroundColor = '#0052a3'
                }}
                onMouseLeave={(e) => {
                  if (hasMatchedFiles && !staging) e.target.style.backgroundColor = '#0066cc'
                }}
              >
                {staging ? 'Staging...' : `Stage ${matchedItems.length} File${matchedItems.length !== 1 ? 's' : ''}`}
              </button>
            )}
          </div>
        </div>
      ) : (
        <div style={{
          padding: '0.5rem 1rem',
          marginBottom: '0.75rem',
          fontSize: '0.9rem',
          color: '#666',
          flexShrink: 0
        }}>
          Select a folder from DSA to view available slides.
        </div>
      )}

      <div style={{ display: 'flex', gap: '1rem', flex: 1, minHeight: 0 }}>
        {/* Left side - Folder Browser */}
        <div style={{ flex: '0 0 400px', minWidth: 0, border: '1px solid #ddd', borderRadius: '6px', padding: '1rem', backgroundColor: '#f8f9fa', overflow: 'auto' }}>
          {authStatus.isAuthenticated ? (
            <FolderBrowser
              apiBaseUrl={authStatus.isConfigured ? getApiUrl('/api/v1') : config.apiBaseUrl}
              apiHeaders={getAuthHeaders()}
              showCollections={true}
              onResourceSelect={handleResourceSelect}
              foldersPerPage={20}
              persistSelection={true}
              persistSelectionKey="deid_folder_selection"
              persistExpansion={true}
              persistExpansionKey="deid_folder_expansion"
            />
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
              Please log in to browse folders and collections.
            </div>
          )}
        </div>

        {/* Right side - Items Table */}
        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', minHeight: 0, border: '1px solid #ddd', borderRadius: '6px', overflow: 'hidden', backgroundColor: '#fff' }}>
          {loading ? (
            <div style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#666',
              backgroundColor: '#f8f9fa'
            }}>
              Loading items...
            </div>
          ) : items.length > 0 ? (
            <div style={{ height: 'calc(100vh - 250px)', width: '100%', minHeight: '400px' }}>
              <AgGridReact
                theme={themeQuartz}
                rowData={items}
                columnDefs={columnDefs}
                defaultColDef={defaultColDef}
                pagination={true}
                paginationPageSize={20}
                paginationAutoPageSize={false}
                domLayout="normal"
                animateRows={true}
                rowSelection="single"
              />
            </div>
          ) : (
            <div style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#666',
              backgroundColor: '#f8f9fa'
            }}>
              {selectedResource?._modelType === 'folder'
                ? 'No items found in this folder'
                : 'Select a folder to view items'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SlidesForDeID

