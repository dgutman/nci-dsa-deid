import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { createPortal } from 'react-dom'
import { useLocation } from 'react-router-dom'
import { AgGridReact } from 'ag-grid-react'
import { ModuleRegistry, AllCommunityModule, themeQuartz } from 'ag-grid-community'
import { useDsaAuth } from 'bdsa-react-components'
import { getAllWSIDeIDItems } from '../utils/wsiDeidUtils'
import config from '../config'

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule])

// Status priority for sorting (lower number = higher priority)
// Processing items first, then recently submitted, then others
const STATUS_PRIORITY = {
  'AvailableToProcess Folder': 1,  // Currently being processed
  'In Redacted Folder': 2,         // Being redacted
  'In Unfiled Folder': 3,           // Recently submitted, waiting to be refiled
  'Submitted': 4,                   // Just submitted
  'In Approved Status': 5,          // Completed
  'In Original Folder': 6,          // In Original folder (not in workflow)
  'DUPLICATE - Already in Workflow': 7,
  'SKIPPED': 8,
  'SKIPPED - Already in Workflow': 8,
  'Invalid Metadata': 9,
  'FileType Not Supported': 9,
  'Unknown': 10
}

// Determine status from path - the third segment of the path is the status
const getStatusFromPath = (path) => {
  if (!path) return 'Unknown'

  // Trim and normalize the path
  path = path.trim()

  // Parse path: /collection/WSI DeID/{status}/...
  // Split on '/' and filter out empty strings
  const parts = path.split('/').filter(p => p.length > 0)

  // Check if this is a WSI DeID collection path and has at least 3 parts
  // parts[0] = 'collection', parts[1] = 'WSI DeID', parts[2] = status folder
  if (parts.length >= 3 && parts[0] === 'collection' && parts[1] === 'WSI DeID') {
    const statusFolder = parts[2] // Third segment is the status

    // Map folder names to status labels
    if (statusFolder === 'Approved') {
      return 'In Approved Status'
    } else if (statusFolder === 'Redacted') {
      return 'In Redacted Folder'
    } else if (statusFolder === 'AvailableToProcess') {
      return 'AvailableToProcess Folder'
    } else if (statusFolder === 'Unfiled') {
      return 'In Unfiled Folder'
    } else if (statusFolder === 'Original') {
      return 'In Original Folder'
    } else {
      // Other folders like Reports, Schema, etc.
      // Check if this is a duplicate (has number suffix like (1), (2), etc.)
      if (path.includes('(') && path.includes(')')) {
        return 'DUPLICATE - Already in Workflow'
      }
      return `In ${statusFolder} Folder`
    }
  }

  return 'Unknown'
}

// Get status priority for sorting
const getStatusPriority = (status) => {
  // Check exact match first
  if (STATUS_PRIORITY[status]) {
    return STATUS_PRIORITY[status]
  }
  // Handle dynamic folder statuses (e.g., "In Reports Folder", "In Schema Folder")
  if (status.startsWith('In ') && status.endsWith(' Folder')) {
    return 6 // Same priority as other non-workflow folders
  }
  return STATUS_PRIORITY['Unknown']
}

function MergedData() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastRefresh, setLastRefresh] = useState(null)
  const [processing, setProcessing] = useState(false)
  const { authStatus, getAuthHeaders, getApiUrl } = useDsaAuth()
  const location = useLocation()

  // Track recently submitted items (from localStorage)
  const [recentlySubmittedIds, setRecentlySubmittedIds] = useState(() => {
    try {
      const stored = localStorage.getItem('deid_recently_submitted')
      return stored ? JSON.parse(stored) : []
    } catch {
      return []
    }
  })

  // Fetch all items from WSI DeID collection with their paths and status
  const fetchMergedData = useCallback(async () => {
    if (!authStatus.isAuthenticated) {
      setItems([])
      return
    }

    setLoading(true)
    setError(null)

    try {
      const apiBaseUrl = authStatus.isConfigured
        ? getApiUrl('/api/v1')
        : config.apiBaseUrl
      const apiHeaders = getAuthHeaders()

      // Fetch all items from WSI DeID collection
      const allItems = await getAllWSIDeIDItems(apiBaseUrl, apiHeaders, {
        onProgress: (progress) => {
          console.log(`Fetched ${progress.fetched} items...`)
        }
      })

      console.log(`Fetched ${allItems.length} items from WSI DeID collection`)

      // Filter out non-image files (.json, .xlsx, .csv)
      const imageExtensions = ['.svs', '.tif', '.tiff', '.jpg', '.jpeg', '.png', '.bmp', '.ndpi', '.vms', '.vmu', '.scn', '.mrxs', '.czi']
      const filteredItems = allItems.filter(item => {
        const fileName = item.name || ''
        const ext = fileName.toLowerCase().substring(fileName.lastIndexOf('.'))
        return imageExtensions.includes(ext)
      })

      console.log(`Filtered to ${filteredItems.length} image files (excluded ${allItems.length - filteredItems.length} non-image files)`)

      // Get recently submitted IDs from localStorage once
      let recentlySubmittedIdsList = []
      try {
        const stored = localStorage.getItem('deid_recently_submitted')
        if (stored) {
          recentlySubmittedIdsList = JSON.parse(stored)
        }
      } catch (e) {
        // Ignore errors reading from localStorage
      }

      // For each item, get its path and determine status
      const itemsWithStatus = await Promise.all(
        filteredItems.map(async (item) => {
          try {
            // Get item path
            const pathResponse = await fetch(
              `${apiBaseUrl}/resource/${item._id}/path?type=item`,
              { headers: apiHeaders }
            )

            let path = null
            if (pathResponse.ok) {
              // The path API returns JSON-encoded string, so parse it
              const pathText = await pathResponse.text()
              if (pathText) {
                // Try to parse as JSON first (it might be a JSON string)
                try {
                  path = JSON.parse(pathText)
                } catch (e) {
                  // If not JSON, use as-is
                  path = pathText
                }
                // Trim whitespace and newlines from path
                if (path) {
                  path = path.trim()
                  // Remove surrounding quotes if present
                  if ((path.startsWith('"') && path.endsWith('"')) ||
                    (path.startsWith("'") && path.endsWith("'"))) {
                    path = path.slice(1, -1)
                  }
                }
              }
            }

            // Determine status from path
            const deidStatus = getStatusFromPath(path)

            // Extract metadata from item.meta.deidUpload if available
            const metadata = item.meta?.deidUpload || {}

            // Check if this item was recently submitted
            const isRecentlySubmitted = recentlySubmittedIdsList.includes(item._id)

            return {
              ...item,
              curDsaPath: path,
              deidStatus,
              statusPriority: getStatusPriority(deidStatus),
              isRecentlySubmitted,
              // Extract metadata fields
              SampleID: metadata.SampleID || '',
              REPOSITORY: metadata.REPOSITORY || '',
              STUDY: metadata.STUDY || '',
              PROJECT: metadata.PROJECT || '',
              CASE: metadata.CASE || '',
              BLOCK: metadata.BLOCK || '',
              ASSAY: metadata.ASSAY || '',
              INDEX: metadata.INDEX || '',
              ImageID: metadata.ImageID || '',
              OutputFileName: metadata.OutputFileName || item.name || '',
              // Timestamp for sorting recently submitted items
              submittedTimestamp: isRecentlySubmitted ? Date.now() : null
            }
          } catch (error) {
            console.error(`Error processing item ${item._id}:`, error)
            return {
              ...item,
              curDsaPath: null,
              deidStatus: 'Unknown',
              statusPriority: getStatusPriority('Unknown'),
              isRecentlySubmitted: false
            }
          }
        })
      )

      // Sort items: processing items first, then recently submitted, then by status priority
      itemsWithStatus.sort((a, b) => {
        // First, prioritize recently submitted items
        if (a.isRecentlySubmitted && !b.isRecentlySubmitted) return -1
        if (!a.isRecentlySubmitted && b.isRecentlySubmitted) return 1

        // If both are recently submitted, sort by timestamp (newest first)
        if (a.isRecentlySubmitted && b.isRecentlySubmitted) {
          return (b.submittedTimestamp || 0) - (a.submittedTimestamp || 0)
        }

        // Then sort by status priority
        if (a.statusPriority !== b.statusPriority) {
          return a.statusPriority - b.statusPriority
        }

        // Finally, sort by name
        return (a.name || '').localeCompare(b.name || '')
      })

      setItems(itemsWithStatus)
      setLastRefresh(new Date())
    } catch (error) {
      console.error('Error fetching merged data:', error)
      setError(error.message)
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [authStatus.isAuthenticated, authStatus.isConfigured])

  // Load recently submitted items from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem('deid_recently_submitted')
      if (stored) {
        const ids = JSON.parse(stored)
        setRecentlySubmittedIds(ids)
      }
    } catch (error) {
      console.error('Error loading recently submitted items:', error)
    }
  }, [])

  // Listen for staging completion to refresh
  useEffect(() => {
    const handleStagingComplete = () => {
      // Reload recently submitted items
      try {
        const stored = localStorage.getItem('deid_recently_submitted')
        if (stored) {
          const ids = JSON.parse(stored)
          setRecentlySubmittedIds(ids)
        }
      } catch (error) {
        console.error('Error loading recently submitted items:', error)
      }
      // Refresh the data
      if (authStatus.isAuthenticated) {
        fetchMergedData()
      }
    }

    window.addEventListener('deid_staging_complete', handleStagingComplete)
    return () => {
      window.removeEventListener('deid_staging_complete', handleStagingComplete)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authStatus.isAuthenticated])

  // Fetch data when:
  // 1. User navigates to this tab (location.pathname is /merged)
  // 2. Auth status changes while on this tab
  useEffect(() => {
    // Only fetch if we're on the merged data tab
    if (location.pathname === '/merged') {
      if (authStatus.isAuthenticated) {
        fetchMergedData()
      } else {
        setItems([])
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authStatus.isAuthenticated, location.pathname])

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
              transform: 'translate(8px, calc(-100% - 8px))',
              zIndex: 10000,
              pointerEvents: 'none',
              maxWidth: `${Math.min(400, window.innerWidth - hoverPosition.x - 40)}px`,
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
      field: 'deidStatus',
      headerName: 'Status',
      width: 200,
      resizable: true,
      sortable: true,
      filter: true,
      cellStyle: (params) => {
        const status = params.value
        const isRecent = params.data?.isRecentlySubmitted

        // Base styles for status
        let backgroundColor = null
        let color = '#333'
        let fontWeight = 'normal'

        if (status === 'AvailableToProcess Folder') {
          backgroundColor = '#FFFD73' // Yellow
        } else if (status === 'In Redacted Folder') {
          backgroundColor = '#FFE073' // Orange
        } else if (status === 'In Approved Status') {
          backgroundColor = '#9DFF73' // Green
        } else if (status === 'In Unfiled Folder' || status === 'Submitted') {
          backgroundColor = '#B3E5FC' // Light blue
          fontWeight = 'bold'
        } else if (status.startsWith('In ') && status.endsWith(' Folder')) {
          // Dynamic folder statuses (Reports, Schema, etc.)
          backgroundColor = '#E0E0E0' // Light gray
        }

        // Highlight recently submitted items
        if (isRecent) {
          backgroundColor = '#FFC107' // Amber highlight
          fontWeight = 'bold'
          color = '#000'
        }

        return {
          backgroundColor,
          color,
          fontWeight
        }
      }
    },
    {
      field: 'name',
      headerName: 'Filename',
      flex: 2,
      resizable: true,
      sortable: true,
      filter: true,
      cellStyle: (params) => {
        if (params.data?.isRecentlySubmitted) {
          return { fontWeight: 'bold' }
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
      filter: true
    },
    {
      field: 'curDsaPath',
      headerName: 'DSA Path',
      flex: 6,
      minWidth: 600,
      resizable: true,
      sortable: true,
      filter: true
    },
    {
      field: 'size',
      headerName: 'File Size',
      width: 120,
      resizable: true,
      sortable: true,
      filter: true,
      valueFormatter: (params) => formatFileSize(params.value)
    },
    {
      field: 'SampleID',
      headerName: 'Sample ID',
      width: 150,
      resizable: true,
      sortable: true,
      filter: true
    },
    {
      field: 'REPOSITORY',
      headerName: 'Repository',
      width: 120,
      resizable: true,
      sortable: true,
      filter: true
    },
    {
      field: 'STUDY',
      headerName: 'Study',
      width: 120,
      resizable: true,
      sortable: true,
      filter: true
    },
    {
      field: 'PROJECT',
      headerName: 'Project',
      width: 120,
      resizable: true,
      sortable: true,
      filter: true
    },
    {
      field: 'CASE',
      headerName: 'Case',
      width: 120,
      resizable: true,
      sortable: true,
      filter: true
    },
    {
      field: 'BLOCK',
      headerName: 'Block',
      width: 100,
      resizable: true,
      sortable: true,
      filter: true
    },
    {
      field: 'ASSAY',
      headerName: 'Assay',
      width: 100,
      resizable: true,
      sortable: true,
      filter: true
    },
    {
      field: 'INDEX',
      headerName: 'Index',
      width: 80,
      resizable: true,
      sortable: true,
      filter: true
    },
    {
      field: 'ImageID',
      headerName: 'Image ID',
      width: 100,
      resizable: true,
      sortable: true,
      filter: true
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
      field: '_id',
      headerName: 'View in DSA',
      width: 120,
      resizable: false,
      sortable: false,
      filter: false,
      pinned: 'right',
      cellRenderer: (params) => {
        if (!params.value) return ''
        const itemId = params.value
        const dsaBaseUrl = import.meta.env.DEV
          ? 'https://wsi-deid.pathology.emory.edu/dsa'
          : '/dsa'
        const dsaUrl = `${dsaBaseUrl}#item/${itemId}`
        return (
          <a
            href={dsaUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: '#0066cc',
              textDecoration: 'underline',
              cursor: 'pointer'
            }}
          >
            Open
          </a>
        )
      }
    }
  ], [])

  const defaultColDef = useMemo(() => ({
    resizable: true,
    sortable: true,
    filter: true
  }), [])

  // Row style for highlighting recently submitted items
  const getRowStyle = (params) => {
    if (params.data?.isRecentlySubmitted) {
      return {
        backgroundColor: '#FFF9C4', // Light yellow background for entire row
        fontWeight: 'bold'
      }
    }
    return null
  }

  // Count items available to process
  const availableToProcessItems = items.filter(item => item.deidStatus === 'AvailableToProcess Folder')
  const availableToProcessCount = availableToProcessItems.length

  // Count items in Redacted status (ready to approve)
  const redactedItems = items.filter(item => item.deidStatus === 'In Redacted Folder')
  const redactedCount = redactedItems.length

  // Process items in AvailableToProcess status (submit for redaction)
  const handleProcessAvailableToProcess = async () => {
    if (availableToProcessCount === 0) {
      alert('No items available to process.')
      return
    }

    if (!confirm(`Process ${availableToProcessCount} item(s) for redaction?`)) {
      return
    }

    setProcessing(true)

    try {
      const apiBaseUrl = authStatus.isConfigured
        ? getApiUrl('/api/v1')
        : config.apiBaseUrl
      const apiHeaders = getAuthHeaders()

      // Get IDs of items to process
      const itemIds = availableToProcessItems.map(item => item._id)

      // Call the batch process endpoint
      const processResponse = await fetch(
        `${apiBaseUrl}/wsi_deid/action/list/process?ids=${encodeURIComponent(JSON.stringify(itemIds))}`,
        {
          method: 'PUT',
          headers: apiHeaders
        }
      )

      if (!processResponse.ok) {
        const errorText = await processResponse.text()
        throw new Error(`Failed to process items: ${processResponse.statusText} - ${errorText}`)
      }

      const result = await processResponse.json()
      console.log('Process result:', result)

      alert(`Successfully submitted ${availableToProcessCount} item(s) for redaction.`)

      // Refresh the data to show updated statuses
      fetchMergedData()
    } catch (error) {
      console.error('Error processing items:', error)
      alert(`Error processing items: ${error.message}`)
    } finally {
      setProcessing(false)
    }
  }

  // Approve items in Redacted status (submit for approval)
  const handleApproveRedacted = async () => {
    if (redactedCount === 0) {
      alert('No items in Redacted folder to approve.')
      return
    }

    if (!confirm(`Approve ${redactedCount} item(s) from Redacted folder?`)) {
      return
    }

    setProcessing(true)

    try {
      const apiBaseUrl = authStatus.isConfigured
        ? getApiUrl('/api/v1')
        : config.apiBaseUrl
      const apiHeaders = getAuthHeaders()

      // Get IDs of items to approve
      const itemIds = redactedItems.map(item => item._id)

      // Call the batch finish endpoint (approve)
      const finishResponse = await fetch(
        `${apiBaseUrl}/wsi_deid/action/list/finish?ids=${encodeURIComponent(JSON.stringify(itemIds))}`,
        {
          method: 'PUT',
          headers: apiHeaders
        }
      )

      if (!finishResponse.ok) {
        const errorText = await finishResponse.text()
        throw new Error(`Failed to approve items: ${finishResponse.statusText} - ${errorText}`)
      }

      const result = await finishResponse.json()
      console.log('Approve result:', result)

      alert(`Successfully approved ${redactedCount} item(s).`)

      // Refresh the data to show updated statuses
      fetchMergedData()
    } catch (error) {
      console.error('Error approving items:', error)
      alert(`Error approving items: ${error.message}`)
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '600px' }}>
      {/* Toolbar */}
      <div style={{
        padding: '0.75rem 1rem',
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
          <span><strong style={{ color: '#0066cc' }}>WSI DeID Collection Status</strong></span>
          {items.length > 0 && (
            <>
              <span style={{ color: '#666' }}>•</span>
              <span style={{ color: '#666' }}>{items.length} item(s)</span>
              {recentlySubmittedIds.length > 0 && (
                <>
                  <span style={{ color: '#666' }}>•</span>
                  <span style={{ color: '#ff6b35', fontWeight: 500 }}>
                    {recentlySubmittedIds.length} recently submitted
                  </span>
                </>
              )}
              {availableToProcessCount > 0 && (
                <>
                  <span style={{ color: '#666' }}>•</span>
                  <span style={{ color: '#FFD700', fontWeight: 500 }}>
                    {availableToProcessCount} available to process
                  </span>
                </>
              )}
              {redactedCount > 0 && (
                <>
                  <span style={{ color: '#666' }}>•</span>
                  <span style={{ color: '#FFE073', fontWeight: 500 }}>
                    {redactedCount} ready to approve
                  </span>
                </>
              )}
            </>
          )}
          {lastRefresh && (
            <>
              <span style={{ color: '#666' }}>•</span>
              <span style={{ color: '#666', fontSize: '0.85rem' }}>
                Last refreshed: {lastRefresh.toLocaleTimeString()}
              </span>
            </>
          )}
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {availableToProcessCount > 0 && (
            <button
              onClick={handleProcessAvailableToProcess}
              disabled={processing || !authStatus.isAuthenticated}
              style={{
                padding: '0.4rem 0.9rem',
                backgroundColor: processing || !authStatus.isAuthenticated ? '#6c757d' : '#FFD700',
                color: processing || !authStatus.isAuthenticated ? '#fff' : '#000',
                border: 'none',
                borderRadius: '4px',
                cursor: processing || !authStatus.isAuthenticated ? 'not-allowed' : 'pointer',
                fontWeight: 600,
                fontSize: '0.85rem',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => {
                if (!processing && authStatus.isAuthenticated) e.target.style.backgroundColor = '#FFC700'
              }}
              onMouseLeave={(e) => {
                if (!processing && authStatus.isAuthenticated) e.target.style.backgroundColor = '#FFD700'
              }}
            >
              {processing ? 'Processing...' : `Process ${availableToProcessCount} for Redaction`}
            </button>
          )}
          {redactedCount > 0 && (
            <button
              onClick={handleApproveRedacted}
              disabled={processing || !authStatus.isAuthenticated}
              style={{
                padding: '0.4rem 0.9rem',
                backgroundColor: processing || !authStatus.isAuthenticated ? '#6c757d' : '#FFE073',
                color: processing || !authStatus.isAuthenticated ? '#fff' : '#000',
                border: 'none',
                borderRadius: '4px',
                cursor: processing || !authStatus.isAuthenticated ? 'not-allowed' : 'pointer',
                fontWeight: 600,
                fontSize: '0.85rem',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => {
                if (!processing && authStatus.isAuthenticated) e.target.style.backgroundColor = '#FFD973'
              }}
              onMouseLeave={(e) => {
                if (!processing && authStatus.isAuthenticated) e.target.style.backgroundColor = '#FFE073'
              }}
            >
              {processing ? 'Approving...' : `Approve ${redactedCount} Items`}
            </button>
          )}
          <button
            onClick={fetchMergedData}
            disabled={loading || !authStatus.isAuthenticated}
            style={{
              padding: '0.4rem 0.9rem',
              backgroundColor: loading || !authStatus.isAuthenticated ? '#6c757d' : '#0066cc',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading || !authStatus.isAuthenticated ? 'not-allowed' : 'pointer',
              fontWeight: 500,
              fontSize: '0.85rem',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => {
              if (!loading && authStatus.isAuthenticated) e.target.style.backgroundColor = '#0052a3'
            }}
            onMouseLeave={(e) => {
              if (!loading && authStatus.isAuthenticated) e.target.style.backgroundColor = '#0066cc'
            }}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Status Legend */}
      <div style={{
        padding: '0.5rem 1rem',
        marginBottom: '0.75rem',
        backgroundColor: '#f8f9fa',
        borderRadius: '4px',
        fontSize: '0.85rem',
        display: 'flex',
        gap: '1rem',
        flexWrap: 'wrap',
        flexShrink: 0
      }}>
        <span><strong>Status Legend:</strong></span>
        <span style={{ backgroundColor: '#FFFD73', padding: '0.2rem 0.5rem', borderRadius: '3px' }}>
          AvailableToProcess
        </span>
        <span style={{ backgroundColor: '#FFE073', padding: '0.2rem 0.5rem', borderRadius: '3px' }}>
          Redacted
        </span>
        <span style={{ backgroundColor: '#9DFF73', padding: '0.2rem 0.5rem', borderRadius: '3px' }}>
          Approved
        </span>
        <span style={{ backgroundColor: '#B3E5FC', padding: '0.2rem 0.5rem', borderRadius: '3px' }}>
          Unfiled/Submitted
        </span>
        <span style={{ backgroundColor: '#FFC107', padding: '0.2rem 0.5rem', borderRadius: '3px', fontWeight: 'bold' }}>
          Recently Submitted
        </span>
      </div>

      {/* AG Grid */}
      {loading ? (
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#666',
          backgroundColor: '#f8f9fa'
        }}>
          Loading items from WSI DeID collection...
        </div>
      ) : error ? (
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#dc3545',
          backgroundColor: '#f8f9fa',
          flexDirection: 'column',
          gap: '1rem'
        }}>
          <div><strong>Error loading data:</strong> {error}</div>
          <button
            onClick={fetchMergedData}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#0066cc',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Retry
          </button>
        </div>
      ) : !authStatus.isAuthenticated ? (
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#666',
          backgroundColor: '#f8f9fa'
        }}>
          Please log in to view WSI DeID collection status.
        </div>
      ) : items.length > 0 ? (
        <div style={{ height: 'calc(100vh - 350px)', width: '100%', minHeight: '400px' }}>
          <AgGridReact
            theme={themeQuartz}
            rowData={items}
            columnDefs={columnDefs}
            defaultColDef={defaultColDef}
            pagination={true}
            paginationPageSize={50}
            paginationAutoPageSize={false}
            domLayout="normal"
            animateRows={true}
            rowSelection="single"
            getRowStyle={getRowStyle}
            suppressRowClickSelection={false}
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
          No items found in WSI DeID collection.
        </div>
      )}
    </div>
  )
}

export default MergedData
