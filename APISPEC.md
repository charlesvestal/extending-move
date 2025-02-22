# File Placer API Specification

## Overview
The File Placer API provides an endpoint for placing files onto the host filesystem. Clients can either:
- Upload a single ZIP file with `mode=zip` to be extracted into a specified destination directory, or
- Upload a non-ZIP file with `mode=place` (or with no mode specified) to simply place the file in the specified destination directory.

## Endpoint

### POST `/place-files`

#### Description
Uploads files to the server and places them at the specified destination paths.

#### Request Modes

Clients can upload a single ZIP file to be extracted into a specified destination directory. Only ZIP mode is supported.

##### ZIP Mode

- **Purpose:** Extract a ZIP archive to a given destination directory.
- **Required Fields:**
  - `mode`: Must be set to `"zip"`.
  - `file`: The ZIP file to be uploaded. (multipart/form-data file field)
  - `destination`: The directory on the host filesystem where the ZIP file contents should be extracted.

#### Responses

##### Success Response (HTTP 200)
- **Content (ZIP mode example):**
```json
{
  "message": "Zip file extracted successfully.",
  "message_type": "success"
}
```

- **Content (Multiple files mode example):**
```json
{
  "message": "Files placed successfully.",
  "message_type": "success"
}
```

##### Error Response (HTTP 4xx/5xx)
- **Content Example:**
```json
{
  "message": "Error description here",
  "message_type": "error"
}
```

#### Example Usage

```bash
curl -X POST http://<server-address>:<port>/place-files \
  -F "mode=zip" \
  -F "file=@/path/to/file.zip" \
  -F "destination=/path/to/extract"
```

#### Example Usage for placing a file (non-ZIP mode):
```bash
curl -X POST http://<server-address>:<port>/place-files \
  -F "mode=place" \
  -F "file=@/path/to/file.txt" \
  -F "destination=/path/to/destination"
```

## Security and Considerations
- **Input Validation:**
  Ensure that destination paths are validated on the server to prevent directory traversal and unauthorized file placements.
- **File Overwrite:**
  Files placed at a destination may overwrite existing files. Clients should verify destination paths to prevent unintended data loss.
- **Authentication & Authorization:**
  This API directly writes to the host filesystem. It should be protected using appropriate authentication and authorization mechanisms to avoid abuse.
- **Error Handling:**
  In case of upload or extraction errors, a descriptive error message is returned. Clients should handle these error responses accordingly.

## Conclusion
The File Placer API offers a flexible and straightforward method for placing files on the host system, either by extracting a ZIP archive or by handling individual file uploads with a mapping to destination directories.

Use this APISPEC.md as a reference for integrating and testing the new File Placer endpoint.
