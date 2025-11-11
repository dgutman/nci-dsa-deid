# WSI DeID API Endpoints Reference

This document lists the available WSI DeID API endpoints that can be used in the application.

## Actions

### Bulk Actions

**PUT** `/wsi_deid/action/bulkRefile`
- Refile multiple images at once.

**PUT** `/wsi_deid/action/export`
- Export recently finished items to the export folder asynchronously.

**PUT** `/wsi_deid/action/exportall`
- Export all finished items to the export folder asynchronously.

**PUT** `/wsi_deid/action/exportreport`
- Generate a report of the items in the system.

**PUT** `/wsi_deid/action/ingest`
- Ingest data from the import folder asynchronously.

**PUT** `/wsi_deid/action/list/{action}`
- Perform an action on a list of items.

**PUT** `/wsi_deid/action/ocrall`
- Run OCR to find label text on items in the import folder without OCR metadata.

## Folder Actions

**PUT** `/wsi_deid/folder/{id}/action/{action}`
- Perform an action on a folder of items.

**POST** `/wsi_deid/folder/{id}/action/refile/{tokenId}`
- Refile items in a folder with a specific token ID.

**GET** `/wsi_deid/folder/{id}/item_list`
- Return a list of all items in a folder with enough information to allow review and redaction.

**GET** `/wsi_deid/folder/{id}/refileList`
- Get the list of known and allowed image names for refiling.

## Item Actions

**PUT** `/wsi_deid/item/{id}/action/{action}`
- Perform an action on an item.

**PUT** `/wsi_deid/item/{id}/action/refile`
- Perform an action on an item.

**POST** `/wsi_deid/item/{id}/action/refile/{tokenId}`
- Refile an item with a specific token ID.

**PUT** `/wsi_deid/item/{id}/redactList`
- Set the redactList meta value on an item.

**GET** `/wsi_deid/item/{id}/refileList`
- Get the list of known and allowed image names for refiling.

**GET** `/wsi_deid/item/{id}/status`
- Get the status of a tracked item.

## Matching

**POST** `/wsi_deid/matching`
- Pass a set of values to the Matching API.

**POST** `/wsi_deid/matching/wsi`
- Simulate the SEER*DMS Matching API for testing.

## Status and Information

**GET** `/wsi_deid/next_unprocessed_folders`
- Get the IDs of the next two folders with unprocessed items and the id of the finished folder.

**GET** `/wsi_deid/next_unprocessed_item`
- Get the ID of the next unprocessed item.

**GET** `/wsi_deid/project_folder/{id}`
- Check if a folder is a project folder.

**GET** `/wsi_deid/resource/{id}/subtreeCount`
- Get total subtree folder and item counts of a resource by ID.

**GET** `/wsi_deid/schema`
- Get the current import schema.

**GET** `/wsi_deid/settings`
- Get settings that affect the UI.

**GET** `/wsi_deid/status`
- Get the status of all tracked items in wsi_deid folders.

## Usage Notes

- All endpoints require authentication via the DSA authentication system
- Replace `{id}` with the actual resource/item/folder ID
- Replace `{action}` with the specific action name
- Replace `{tokenId}` with the token ID for refiling operations
- Base URL should be configured via the `apiBaseUrl` in the application config

