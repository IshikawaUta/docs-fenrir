# File Upload

Fenrir provides the `UploadFile` class for handling file uploads. It wraps file-like objects and transparently supports both sync and async file backends.

## UploadFile

### Attributes

| Attribute     | Type          | Description                                      |
|---------------|---------------|--------------------------------------------------|
| `filename`    | `str`         | The original filename of the uploaded file.       |
| `file`        | `SpooledTemporaryFile` | The underlying file-like object.          |
| `content_type`| `str`         | The MIME type of the uploaded file.               |

### Methods

All methods are `async` and internally handle both sync and async file objects transparently — you call them the same way regardless of the underlying file type.

#### `read(size=-1) -> bytes`

Read up to `size` bytes from the file. If `size` is `-1` (the default), the entire file is read.

```python
contents = await file.read()       # entire file
chunk = await file.read(1024)      # first 1024 bytes
```

#### `write(data: bytes)`

Write `data` bytes to the file.

```python
await file.write(b"hello world")
```

#### `seek(offset: int)`

Move the file pointer to the given byte offset.

```python
await file.seek(0)   # rewind to beginning
```

#### `close()`

Close the underlying file. If the file object has no `close` method this is a no-op.

```python
await file.close()
```

---

## Examples

### Single File Upload

```python
from fenrir import File, UploadFile

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    return {
        "filename": file.filename,
        "size": len(contents),
        "content_type": file.content_type
    }
```

### Multiple Files Upload

```python
from typing import List
from fenrir import File, UploadFile

@app.post("/upload-multiple")
async def upload_multiple(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        contents = await file.read()
        results.append({
            "filename": file.filename,
            "size": len(contents)
        })
    return results
```

### File Upload with Form Data

```python
from fenrir import Form, File, UploadFile

@app.post("/upload-with-form")
async def upload_with_form(
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...)
):
    contents = await file.read()
    return {
        "title": title,
        "description": description,
        "filename": file.filename,
        "file_size": len(contents)
    }
```

### Save Uploaded Files

```python
import os
from fenrir import UploadFile, File

@app.post("/save-file")
async def save_file(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)

    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        contents = await file.read()
        f.write(contents)

    return {"message": "File saved", "path": file_path}
```

### Seek and Re-read

```python
from fenrir import File, UploadFile

@app.post("/upload-validate")
async def upload_validate(file: UploadFile = File(...)):
    contents = await file.read()

    # Validate the file content
    if len(contents) == 0:
        return {"error": "Empty file"}

    # Seek back and read again to demonstrate seek support
    await file.seek(0)
    reread = await file.read()

    assert contents == reread
    return {"filename": file.filename, "size": len(contents)}
```

### Write to an UploadFile

```python
from fenrir import File, UploadFile

@app.post("/upload-modify")
async def upload_modify(file: UploadFile = File(...)):
    original = await file.read()

    # Write additional data
    await file.seek(0)
    await file.write(b"PREFIX:" + original)

    await file.seek(0)
    modified = await file.read()

    return {"modified_size": len(modified)}
```

---

## Serving Files

### send_file

Send a file from the filesystem as a response. Automatically detects MIME type.

```python
from fenrir import send_file

@app.get("/download/<filename>")
async def download(filename: str):
    return send_file(f"uploads/{filename}")

# As attachment (forces download)
@app.get("/attachment/<filename>")
async def attachment(filename: str):
    return send_file(f"uploads/{filename}", as_attachment=True)

# With custom MIME type
@app.get("/data")
async def data_file():
    return send_file("data.bin", mimetype="application/octet-stream")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path_or_file` | `str \| File` | *required* | File path string or file-like object |
| `mimetype` | `str` | `None` | MIME type (auto-detected if omitted) |
| `as_attachment` | `bool` | `False` | Force download with `Content-Disposition: attachment` |
| `download_name` | `str` | `None` | Filename for the `Content-Disposition` header |

### send_from_directory

Send a file from a specific directory with path traversal protection.

```python
from fenrir import send_from_directory

@app.get("/static/<path:filename>")
async def serve_static(filename: str):
    return send_from_directory("static", filename)

@app.get("/uploads/<path:filename>")
async def serve_upload(filename: str):
    return send_from_directory("uploads", filename)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `directory` | `str` | *required* | Directory path to serve files from |
| `path` | `str` | *required* | Relative file path within the directory |
| `**kwargs` | | | Additional arguments passed to `send_file` |

---

## Redirect Helper

The `redirect` function returns a `RedirectResponse` with path resolution for relative URLs.

```python
from fenrir import redirect

@app.get("/old-page")
async def old_page():
    return redirect("/new-page")  # 302 redirect

@app.get("/login")
async def login():
    return redirect("/dashboard", code=303)  # 303 redirect after POST
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `location` | `str` | *required* | URL to redirect to |
| `code` | `int` | `302` | HTTP redirect status code |
