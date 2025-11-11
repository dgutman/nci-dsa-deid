# ReactDeID Service

A React + Vite application for the NCI DSA DeID workflow, replacing the Python/Dash implementation.

## Development

### Local Development (outside Docker)

**Important:** Due to a missing peer dependency (`osd-paperjs-annotation`), you need to install with the `--legacy-peer-deps` flag:

```bash
cd services/reactdeid
npm install --legacy-peer-deps
npm run dev
```

The app will be available at `http://localhost:5173/` (no `/deid/` needed for local dev)

**Note:** Once `osd-paperjs-annotation` is published to npm, this workaround will no longer be needed.

### Docker Development

The service is configured in `devops/nci-dsa-deid/docker-compose.yml` and will be available at:
- Through nginx: `http://localhost:8090/deid/`
- Direct access: `http://localhost:5173/deid/`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Architecture

- **Framework**: React 18 with Vite
- **Routing**: React Router v6
- **Data Fetching**: TanStack Query (React Query)
- **Tables**: AG Grid React
- **Validation**: AJV for JSON schema validation
- **CSV Parsing**: PapaParse

## Pages

- `/slides` - Slides For DeID (file browser)
- `/metadata` - Slide Metadata upload
- `/merged` - Merged Data view with validation
- `/instructions` - Usage instructions

## Configuration

### Environment Variables

The app uses environment variables for configuration. Create a `.env.local` file (gitignored) for your local development settings:

```bash
# Copy the example file
cp .env.local.example .env.local

# Edit .env.local with your settings
VITE_DSA_API_URL=http://bdsa.pathology.emory.edu:8080/api/v1
```

**Configuration Options:**

- `VITE_DSA_API_URL` - DSA/Girder API URL
  - **Local Dev (default):** `http://bdsa.pathology.emory.edu:8080/api/v1` (remote instance)
  - **Production:** `/dsa/api/v1` (uses nginx proxy)
  - **Custom:** Set to any DSA instance URL

- `VITE_DSA_PROXY_TARGET` - Target URL for Vite proxy (only used if using relative `/dsa` path)
  - Default: `http://localhost:8080`

**Note:** 
- In **development mode**, the app defaults to connecting to a remote DSA instance (`http://bdsa.pathology.emory.edu:8080/api/v1`)
- In **production mode** (Docker), it uses the relative path `/dsa/api/v1` which nginx proxies to the girder service
- You can override the default by setting `VITE_DSA_API_URL` in your `.env.local` file

## Migration from Dash

This service is replacing the Python/Dash `dashdeid` service. During migration:
- New React app: `/deid/` (via nginx)
- Old Dash app: `/dashdeid/` (via nginx) or direct port `8050`

