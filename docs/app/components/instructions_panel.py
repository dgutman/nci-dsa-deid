from dash import dcc, html
import dash_bootstrap_components as dbc


app_instructions = dcc.Markdown(
    """## **Instructions for using the NCI DeID Upload Agent**

### **1. Login:**
- At the top-right corner of the application, you'll find the **Login** section.
- Enter your **Username** and **Password** in the respective fields.
- Click the **Login** button to authenticate. If the credentials are valid, you'll receive a "Login successful" notification. If not, a modal will pop up indicating an error.

### **2. Select DSA Folder:**
- Click on the **DSA Folder** button to open a modal that lets you select a Digital Slide Archive (DSA) folder.
- Navigate through the folder structure and select the desired folder by clicking on it.

### **3. Upload Metadata:**
- Navigate to the **Metadata** tab.
- Here you can upload your metadata file:
  - Drag and drop your file into the designated area, or
  - Click on the area and select your file from the file dialog.
- The app currently supports `.csv`, `.xls`, and `.xlsx` file formats.
- Once uploaded, the metadata will be parsed and displayed in a table format below the upload area.

### **4. Debug Tools:**
- For developers and testers, there's a **Debug Tools** tab.
- Here you can perform actions like loading test data.
  
### **5. Merged Data:**
- In the **merged Data** tab, you can view the combined data from the metadata and the DSA folder.
- Rows with a match between the DSA folder and the metadata will be highlighted.
- You can submit matched images for DeID by clicking the **Submit for DeID** button.

### **6. View Logs:**
- There's a **Logs** button that, when clicked, displays a scrollable log of actions and errors in the app. This is especially useful for debugging and tracking user actions.

### **7. Logout and Exit:**
- After completing your tasks, ensure you log out for security reasons.
- Close the application window or browser tab to exit.
""",
    # style={
    #     "fontSize": "13px",  # Adjust as needed
    #     "lineHeight": "1.0",  # Adjust the number for line spacing
    #     "height": "auto",
    # },
)


file_format_instructions = dcc.Markdown(
    """## Instructions for Uploading Metadata to the NCI DeID App

### File Format

The NCI DeID App supports metadata uploads in both CSV and Excel (XLS, XLSX) formats. The file must be properly structured with specific column headers.

### Required Columns

The following columns are required in the metadata file:

- **InputFileName**: The name of the original file. (e.g., `17202566.svs`)
- **SampleID**: A unique identifier for the sample. (e.g., `RS22-60259`)
- **REPOSITORY**: The repository where the sample is stored. (e.g., `FNLCR`)
- **STUDY**: The study related to the sample. (e.g., `Visium`)
- **PROJECT**: The project code or identifier. (e.g., `232378`)
- **CASE**: The case identifier (can be blank).
- **BLOCK**: The block identifier. (e.g., `B1`)
- **ASSAY**: The type of assay. (e.g., `H&E`)
- **INDEX**: The index of the sample (can be blank).
- **ImageID**: A unique identifier for the image. (e.g., `17202566`)
- **OutputFileName**: The name of the output file. (e.g., `17202566.svs`)

### Sample Data

Here's an example of the data format:

    InputFileName,SampleID,REPOSITORY,STUDY,PROJECT,CASE,BLOCK,ASSAY,INDEX,ImageID,OutputFileName
    17202566.svs,RS22-60259,FNLCR,Visium,232378,,B1,H&E,,17202566,17202566.svs
    17199575.svs,RS20-1704,FNLCR,Visium,232366,,B1,H&E,,17199575,17199575.svs


### Uploading the File

1. Navigate to the **Metadata** tab in the NCI DeID App.
2. Drag and drop your CSV or Excel file, or click to select the file from your computer.
3. The app will validate the file structure and contents. Ensure all required columns are present and filled out as necessary.
4. If there are issues with the file, appropriate error messages will be displayed. Address these issues and re-upload.

By following these instructions, you ensure that your metadata is correctly processed and integrated with the NCI DeID system.

"""
)


instructions_panel = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [app_instructions],
                style={
                    "height": "500px",  # You can adjust this value to your desired height
                    # "flex": "1",
                    "overflow-y": "auto",
                },
            ),
        ]
    ),
    className="mt-3",
)
