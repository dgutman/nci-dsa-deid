import './Instructions.css'

function Instructions() {
  return (
    <div className="instructions-container">
      <div className="instructions-card">
        <div className="instructions-content">
          <h2>Instructions for using the NCI DeID Upload Agent</h2>

          <h3>1. Login:</h3>
          <ul>
            <li>At the top-right corner of the application, you'll find the <strong>Login</strong> section.</li>
            <li>Enter your <strong>Username</strong> and <strong>Password</strong> in the respective fields.</li>
            <li>Click the <strong>Login</strong> button to authenticate. If the credentials are valid, you'll receive a "Login successful" notification. If not, a modal will pop up indicating an error.</li>
          </ul>

          <h3>2. Select DSA Folder:</h3>
          <ul>
            <li>Navigate to the <strong>Slides For DeID</strong> tab.</li>
            <li>Browse through the folder structure and select a folder containing the slides you want to process.</li>
            <li>Once a folder is selected, the app will display the number of items found in that folder.</li>
            <li>If there are unmatched files (files without corresponding metadata), you can download a template CSV file by clicking the <strong>Download Template</strong> button.</li>
          </ul>

          <h3>3. Download Template (Optional):</h3>
          <ul>
            <li>After selecting a DSA folder, if there are files without matching metadata, a <strong>Download Template</strong> button will appear.</li>
            <li>Click this button to download a CSV template file containing all unmatched files.</li>
            <li>The template includes pre-filled columns with placeholder values that you can edit:</li>
            <ul>
              <li><strong>InputFileName</strong>: The original filename from DSA (automatically filled)</li>
              <li><strong>SampleID</strong>: A generated sample identifier (you can customize this)</li>
              <li><strong>REPOSITORY</strong>: Default repository value (e.g., <code>DCEG</code>)</li>
              <li><strong>STUDY</strong>: Default study value (e.g., <code>MR-0600</code>)</li>
              <li><strong>PROJECT</strong>: Default project code (e.g., <code>HP0600-001</code>)</li>
              <li><strong>CASE</strong>: Default case identifier (e.g., <code>TestProject</code>)</li>
              <li><strong>BLOCK</strong>: Auto-generated block identifier (e.g., <code>BR0001</code>)</li>
              <li><strong>ASSAY</strong>: Default assay type (e.g., <code>H&amp;E</code>)</li>
              <li><strong>INDEX</strong>: Sequential index number</li>
              <li><strong>ImageID</strong>: Default image identifier (e.g., <code>SA</code>)</li>
              <li><strong>OutputFileName</strong>: Auto-generated output filename based on SampleID</li>
            </ul>
            <li>Edit the template file with your actual metadata values, then upload it in the <strong>Metadata</strong> tab.</li>
          </ul>

          <h3>4. Upload Metadata:</h3>
          <ul>
            <li>Navigate to the <strong>Metadata</strong> tab.</li>
            <li>Here you can upload your metadata file:
              <ul>
                <li>Drag and drop your file into the designated area, or</li>
                <li>Click on the area and select your file from the file dialog.</li>
              </ul>
            </li>
            <li>The app currently supports <code>.csv</code>, <code>.xls</code>, and <code>.xlsx</code> file formats.</li>
            <li>Once uploaded, the metadata will be parsed and displayed in a table format below the upload area.</li>
          </ul>

          <h3>5. Debug Tools:</h3>
          <ul>
            <li>For developers and testers, there's a <strong>Debug Tools</strong> tab.</li>
            <li>Here you can perform actions like loading test data.</li>
          </ul>

          <h3>6. Merged Data:</h3>
          <ul>
            <li>In the <strong>merged Data</strong> tab, you can view the combined data from the metadata and the DSA folder.</li>
            <li>Rows with a match between the DSA folder and the metadata will be highlighted.</li>
            <li>You can submit matched images for DeID by clicking the <strong>Submit for DeID</strong> button.</li>
          </ul>

          <h3>7. View Logs:</h3>
          <ul>
            <li>There's a <strong>Logs</strong> button that, when clicked, displays a scrollable log of actions and errors in the app. This is especially useful for debugging and tracking user actions.</li>
          </ul>

          <h3>8. Logout and Exit:</h3>
          <ul>
            <li>After completing your tasks, ensure you log out for security reasons.</li>
            <li>Close the application window or browser tab to exit.</li>
          </ul>

          <hr className="instructions-divider" />

          <h2>Instructions for Uploading Metadata to the NCI DeID App</h2>

          <h3>File Format</h3>
          <p>
            The NCI DeID App supports metadata uploads in both CSV and Excel (XLS, XLSX) formats. The file must be properly structured with specific column headers.
          </p>

          <h3>Required Columns</h3>
          <p>The following columns are required in the metadata file:</p>
          <ul>
            <li><strong>InputFileName</strong>: The name of the original file. (e.g., <code>17202566.svs</code>)</li>
            <li><strong>SampleID</strong>: A unique identifier for the sample. (e.g., <code>RS22-60259</code>)</li>
            <li><strong>REPOSITORY</strong>: The repository where the sample is stored. (e.g., <code>FNLCR</code>)</li>
            <li><strong>STUDY</strong>: The study related to the sample. (e.g., <code>Visium</code>)</li>
            <li><strong>PROJECT</strong>: The project code or identifier. (e.g., <code>232378</code>)</li>
            <li><strong>CASE</strong>: The case identifier (can be blank).</li>
            <li><strong>BLOCK</strong>: The block identifier. (e.g., <code>B1</code>)</li>
            <li><strong>ASSAY</strong>: The type of assay. (e.g., <code>H&amp;E</code>)</li>
            <li><strong>INDEX</strong>: The index of the sample (can be blank).</li>
            <li><strong>ImageID</strong>: A unique identifier for the image. (e.g., <code>17202566</code>)</li>
            <li><strong>OutputFileName</strong>: The name of the output file. (e.g., <code>17202566.svs</code>)</li>
          </ul>

          <h3>Sample Data</h3>
          <p>Here's an example of the data format:</p>
          <pre className="sample-data">
            <code>
{`InputFileName,SampleID,REPOSITORY,STUDY,PROJECT,CASE,BLOCK,ASSAY,INDEX,ImageID,OutputFileName
17202566.svs,RS22-60259,FNLCR,Visium,232378,,B1,H&E,,17202566,17202566.svs
17199575.svs,RS20-1704,FNLCR,Visium,232366,,B1,H&E,,17199575,17199575.svs`}
            </code>
          </pre>

          <h3>Uploading the File</h3>
          <ol>
            <li>Navigate to the <strong>Metadata</strong> tab in the NCI DeID App.</li>
            <li>Drag and drop your CSV or Excel file, or click to select the file from your computer.</li>
            <li>The app will validate the file structure and contents. Ensure all required columns are present and filled out as necessary.</li>
            <li>If there are issues with the file, appropriate error messages will be displayed. Address these issues and re-upload.</li>
          </ol>

          <p>
            By following these instructions, you ensure that your metadata is correctly processed and integrated with the NCI DeID system.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Instructions

