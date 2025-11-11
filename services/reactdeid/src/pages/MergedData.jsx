import { useState, useEffect, useMemo, useCallback } from 'react'
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
  'In Collection (Not in Workflow)': 6,  // In WSI DeID collection but not in workflow folders
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
  
  // Parse path: /collection/WSI DeID/{status}/...
  const parts = path.split('/').filter(p => p.length > 0)
  
  // Check if this is a WSI DeID collection path
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
              path = await pathResponse.text()
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

  // AG Grid column definitions
  const columnDefs = useMemo(() => [
    {
      field: 'deidStatus',
      headerName: 'Status',
      width: 200,
      resizable: true,
      sortable: true,
      filter: true,
      pinned: 'left',
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
