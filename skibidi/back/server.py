from fastapi import FastAPI, UploadFile, File, Form
from parser import parse_pdf
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), question: str = Form("")):

    pdf_bytes = await file.read()

    result = parse_pdf(pdf_bytes, question)
    print(result)

    return result

