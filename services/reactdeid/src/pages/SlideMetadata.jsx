import { useState, useEffect } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ModuleRegistry, AllCommunityModule, themeQuartz } from 'ag-grid-community'
import Papa from 'papaparse'

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule])

function SlideMetadata() {
  const [metadata, setMetadata] = useState([])
  const [fileName, setFileName] = useState(null)
  const [folderItems, setFolderItems] = useState([])

  // Listen for folder items updates from SlidesForDeID page
  useEffect(() => {
    const checkFolderItems = () => {
      try {
        const stored = localStorage.getItem('deid_selected_folder_items')
        if (stored) {
          const items = JSON.parse(stored)
          setFolderItems(items)
        }
      } catch (error) {
        console.error('Error reading folder items:', error)
      }
    }

    // Check for metadata generated from SlidesForDeID DEV button
    const checkGeneratedMetadata = () => {
      try {
        const storedMetadata = localStorage.getItem('deid_metadata')
        const storedFilename = localStorage.getItem('deid_metadata_filename')
        if (storedMetadata && storedFilename) {
          const metadata = JSON.parse(storedMetadata)
          setMetadata(metadata)
          setFileName(storedFilename)
        }
      } catch (error) {
        console.error('Error reading generated metadata:', error)
      }
    }

    // Check on mount
    checkFolderItems()
    checkGeneratedMetadata()

    // Listen for storage changes
    window.addEventListener('storage', () => {
      checkFolderItems()
      checkGeneratedMetadata()
    })
    
    // Poll for changes (since storage event doesn't fire in same window)
    const interval = setInterval(() => {
      checkFolderItems()
      checkGeneratedMetadata()
    }, 1000)

    return () => {
      window.removeEventListener('storage', () => {
        checkFolderItems()
        checkGeneratedMetadata()
      })
      clearInterval(interval)
    }
  }, [])

  const handleFileUpload = (event) => {
    const file = event.target.files[0]
    if (!file) return

    setFileName(file.name)

    if (file.name.endsWith('.csv')) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const text = e.target.result
        const parsed = Papa.parse(text, { header: true, skipEmptyLines: true })
        setMetadata(parsed.data)
        localStorage.setItem('deid_metadata', JSON.stringify(parsed.data))
        localStorage.setItem('deid_metadata_filename', file.name)
        // Dispatch custom event to notify other components
        window.dispatchEvent(new Event('deid_metadata_updated'))
      }
      reader.readAsText(file)
    } else if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
      // TODO: Add Excel parsing support
      alert('Excel file support coming soon. Please use CSV for now.')
    }
  }

  const handleDevLoad = () => {
    if (folderItems.length === 0) {
      alert('No folder selected. Please go to "Slides For DeID" tab and select a folder first.')
      return
    }

    // Generate metadata from folder items (same logic as download template)
    const today = new Date()
    const batchId = `Batch-${today.getFullYear()}${String(today.getMonth() + 1).padStart(2, '0')}${String(today.getDate()).padStart(2, '0')}`

    const generatedMetadata = folderItems.map((item, index) => {
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
        const baseName = filename.replace(/\.svs$/, '')
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

    setMetadata(generatedMetadata)
    setFileName(`Generated from folder (${folderItems.length} items) [DEV]`)
    localStorage.setItem('deid_metadata', JSON.stringify(generatedMetadata))
    localStorage.setItem('deid_metadata_filename', `Generated from folder (${folderItems.length} items) [DEV]`)
    // Dispatch custom event to notify other components
    window.dispatchEvent(new Event('deid_metadata_updated'))
  }

  const columnDefs = metadata.length > 0 
    ? Object.keys(metadata[0]).map(key => ({
        field: key,
        headerName: key,
        resizable: true,
        sortable: true,
        filter: true
      }))
    : []

  const defaultColDef = {
    resizable: true,
    sortable: true,
    filter: true
  }

  return (
    <div>
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <div style={{ flex: 1 }}>
          <label
            htmlFor="file-upload"
            style={{
              display: 'inline-block',
              padding: '0.75rem 1.5rem',
              backgroundColor: '#0066cc',
              color: 'white',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 500,
              fontSize: '0.9rem',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#0052a3'}
            onMouseLeave={(e) => e.target.style.backgroundColor = '#0066cc'}
          >
            Upload Metadata File
          </label>
          <input
            id="file-upload"
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
        </div>
        <button
          onClick={handleDevLoad}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: '#ff6b35',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: 500,
            fontSize: '0.9rem',
            transition: 'background-color 0.2s'
          }}
          onMouseEnter={(e) => e.target.style.backgroundColor = '#e55a2b'}
          onMouseLeave={(e) => e.target.style.backgroundColor = '#ff6b35'}
        >
          [DEV] Load Test Data
        </button>
      </div>

      {fileName && (
        <div style={{ marginBottom: '1rem', padding: '0.5rem 1rem', backgroundColor: '#e8f4f8', borderRadius: '6px', fontSize: '0.9rem' }}>
          <strong>Loaded:</strong> {fileName} ({metadata.length} rows)
        </div>
      )}

      {metadata.length > 0 ? (
        <div style={{ height: 'calc(100vh - 300px)', width: '100%', minHeight: '400px' }}>
          <AgGridReact
            theme={themeQuartz}
            rowData={metadata}
            columnDefs={columnDefs}
            defaultColDef={defaultColDef}
            pagination={true}
            paginationPageSize={20}
            paginationAutoPageSize={false}
            domLayout="normal"
            animateRows={true}
          />
        </div>
      ) : (
        <div style={{
          padding: '3rem',
          textAlign: 'center',
          color: '#666',
          border: '2px dashed #ddd',
          borderRadius: '6px',
          backgroundColor: '#f8f9fa'
        }}>
          <p style={{ margin: 0, fontSize: '1rem' }}>
            Please upload a metadata file (CSV, XLS, XLSX) or click <strong>[DEV] Load Test Data</strong> to load example data.
          </p>
        </div>
      )}
    </div>
  )
}

export default SlideMetadata

