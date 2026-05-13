import os
import uuid

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from models import User
from utils.security import get_current_user, require_roles

router = APIRouter()


@router.post("/uploads/report-photo")
async def upload_report_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a report photo to Appwrite Storage and return its view URL."""
    require_roles(
        current_user,
        {"cell_leader", "senior_cell_leader", "fellowship_pastor", "zonal_admin", "system_admin"},
    )

    endpoint = os.getenv("APPWRITE_ENDPOINT", "").rstrip("/")
    project_id = os.getenv("APPWRITE_PROJECT_ID", "")
    api_key = os.getenv("APPWRITE_API_KEY", "")
    bucket_id = os.getenv("APPWRITE_BUCKET_ID", "")

    if not all([endpoint, project_id, api_key, bucket_id]):
        raise HTTPException(
            status_code=500,
            detail="Appwrite storage is not configured on the backend",
        )

    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    content = await file.read()
    if len(content) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be 8MB or smaller")

    file_id = uuid.uuid4().hex
    upload_url = f"{endpoint}/storage/buckets/{bucket_id}/files"

    try:
      async with httpx.AsyncClient(timeout=60) as client:
          response = await client.post(
              upload_url,
              headers={
                  "X-Appwrite-Project": project_id,
                  "X-Appwrite-Key": api_key,
              },
              data=[
                  ("fileId", file_id),
                  ("permissions[]", 'read("any")'),
              ],
              files={
                  "file": (
                      file.filename or f"{file_id}.jpg",
                      content,
                      file.content_type or "image/jpeg",
                  )
              },
          )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Photo upload failed: {exc}") from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Photo upload failed: {response.text}")

    view_url = (
        f"{endpoint}/storage/buckets/{bucket_id}/files/{file_id}/view"
        f"?project={project_id}"
    )

    return {
        "file_id": file_id,
        "url": view_url,
    }
