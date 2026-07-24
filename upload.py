from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "message": "Image received successfully"
    }