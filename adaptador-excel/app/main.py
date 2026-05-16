import logging

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.consumer import consumer
from app.excel_writer import EXCEL_FILE_PATH, ensure_workbook, workbook_info


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="Adaptador Excel")


@app.on_event("startup")
async def startup() -> None:
    await consumer.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    await consumer.stop()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "adaptador-excel"}


@app.get("/excel/status")
async def excel_status() -> dict:
    return workbook_info()


@app.get("/excel/download")
async def excel_download() -> FileResponse:
    ensure_workbook()
    return FileResponse(
        EXCEL_FILE_PATH,
        filename="promociones.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
