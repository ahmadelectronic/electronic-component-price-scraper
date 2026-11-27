"""Local HTML dashboard for the electronic-component price monitor."""

from __future__ import annotations

import logging
import threading
import webbrowser
from io import BytesIO
from pathlib import Path
from typing import Any
from threading import Timer

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

from . import PriceMonitor, ScraperConfig

logger = logging.getLogger(__name__)

# Keep the workbook and reports in the project launch directory.
PROJECT_DIR = Path.cwd().resolve()
DATABASE_FILE = PROJECT_DIR / "database.xlsx"
OUTPUT_FILE = PROJECT_DIR / "output.xlsx"
HISTORY_FILE = PROJECT_DIR / "price_history.xlsx"
TEMPLATE_FILE = Path(__file__).parent / "templates" / "index.html"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_ROWS = 10_000


app = FastAPI(
    title="Electronic Component Price Monitor",
    docs_url=None,
    redoc_url=None,
)

_job_lock = threading.Lock()
_job: dict[str, Any] = {
    "status": "idle",
    "completed": 0,
    "total": 0,
    "progress": 0,
    "message": "آمادهٔ شروع",
    "rows": [],
    "summary": None,
    "error": None,
}


class SpreadsheetPayload(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]


class RunPayload(BaseModel):
    workers: int = Field(default=10, ge=1, le=64)
    timeout: float = Field(default=15, gt=0, le=120)


def _safe_value(value: Any) -> Any:
    """Convert pandas/numpy values to JSON-friendly Python values."""
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (ValueError, TypeError):
            pass
    if hasattr(value, "isoformat") and not isinstance(value, str):
        try:
            return value.isoformat()
        except (ValueError, TypeError):
            pass
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _clean_frame(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.copy()
    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    if len(set(dataframe.columns)) != len(dataframe.columns):
        raise ValueError("نام ستون‌ها نباید تکراری باشد.")
    missing = {"Supplier", "Quantity"}.difference(dataframe.columns)
    if missing:
        raise ValueError(
            "فایل باید ستون‌های Supplier و Quantity را داشته باشد. "
            f"ستون‌های پیدا‌شده: {list(dataframe.columns)}"
        )
    if len(dataframe) > MAX_ROWS:
        raise ValueError(f"حداکثر تعداد ردیف مجاز {MAX_ROWS:,} است.")
    return dataframe


def _read_database() -> pd.DataFrame:
    if not DATABASE_FILE.exists():
        return pd.DataFrame(columns=["Supplier", "Quantity"])
    try:
        return _clean_frame(pd.read_excel(DATABASE_FILE))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"خواندن فایل Excel ناموفق بود: {exc}") from exc


def _frame_payload(dataframe: pd.DataFrame) -> dict[str, Any]:
    rows = [
        {str(key): _safe_value(value) for key, value in record.items()}
        for record in dataframe.to_dict(orient="records")
    ]
    return {"columns": list(dataframe.columns), "rows": rows, "count": len(rows)}


def _snapshot_job() -> dict[str, Any]:
    with _job_lock:
        # Return a detached snapshot so API clients cannot mutate worker state.
        return {
            **_job,
            "rows": [dict(row) for row in _job.get("rows", [])],
            "summary": dict(_job["summary"]) if _job.get("summary") else None,
        }


def _result_payload(result: Any) -> dict[str, Any]:
    return {
        "status": result.status,
        "price": result.price,
        "total_price": result.total_price,
        "error": result.error,
    }


def _run_worker(workers: int, timeout: float) -> None:
    def on_progress(index: int, completed: int, total: int, result: Any) -> None:
        with _job_lock:
            if 0 <= index < len(_job["rows"]):
                _job["rows"][index].update(_result_payload(result))
            _job["completed"] = completed
            _job["total"] = total
            _job["progress"] = int(completed * 100 / total) if total else 100
            _job["message"] = f"{completed:,} از {total:,} کالا بررسی شد"

    try:
        config = ScraperConfig(
            input_file=DATABASE_FILE,
            output_file=OUTPUT_FILE,
            history_file=HISTORY_FILE,
            max_workers=workers,
            timeout=timeout,
            auto_open=False,
            show_progress=False,
        )
        summary = PriceMonitor(config).run(progress_callback=on_progress)
        summary_data = {
            "total_records": summary.total_records,
            "successful": summary.successful,
            "not_found": summary.not_found,
            "errors": summary.errors,
            "grand_total": summary.grand_total,
            "output_file": str(summary.output_file.name),
            "history_file": str(summary.history_file.name),
        }
        with _job_lock:
            _job["status"] = "completed"
            _job["progress"] = 100
            _job["message"] = "بررسی قیمت‌ها با موفقیت تمام شد"
            _job["summary"] = summary_data
    except Exception as exc:  # Keep the server alive and return a useful UI error.
        logger.exception("Web dashboard scraping job failed")
        with _job_lock:
            _job["status"] = "error"
            _job["message"] = "اجرای بررسی با خطا متوقف شد"
            _job["error"] = str(exc)


@app.get("/", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    try:
        html = TEMPLATE_FILE.read_text(encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail="فایل رابط کاربری پیدا نشد.") from exc
    return HTMLResponse(html)


@app.get("/api/data")
async def get_data() -> dict[str, Any]:
    return _frame_payload(_read_database())


@app.post("/api/data")
async def save_data(payload: SpreadsheetPayload) -> dict[str, Any]:
    if not payload.columns:
        raise HTTPException(status_code=422, detail="ستون‌های فایل خالی است.")
    if len(payload.rows) > MAX_ROWS:
        raise HTTPException(status_code=422, detail=f"حداکثر تعداد ردیف مجاز {MAX_ROWS:,} است.")
    columns = [str(column).strip() for column in payload.columns]
    if len(set(columns)) != len(columns):
        raise HTTPException(status_code=422, detail="نام ستون‌ها نباید تکراری باشد.")
    try:
        dataframe = _clean_frame(pd.DataFrame(payload.rows, columns=columns))
        DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
        dataframe.to_excel(DATABASE_FILE, index=False)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True, "message": "اطلاعات ذخیره شد.", "count": len(dataframe)}


@app.post("/api/upload")
async def upload_excel(file: UploadFile = File(...)) -> dict[str, Any]:
    filename = (file.filename or "").lower()
    if not filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="فقط فایل Excel با پسوند .xlsx پشتیبانی می‌شود.")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="حجم فایل باید کمتر از ۱۰ مگابایت باشد.")
    try:
        dataframe = _clean_frame(pd.read_excel(BytesIO(content)))
        DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
        dataframe.to_excel(DATABASE_FILE, index=False)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"فایل Excel معتبر نیست: {exc}") from exc
    return {"ok": True, "message": "فایل با موفقیت بارگذاری شد.", **_frame_payload(dataframe)}


@app.post("/api/run")
async def start_run(payload: RunPayload) -> dict[str, Any]:
    dataframe = _read_database()
    if dataframe.empty:
        raise HTTPException(status_code=400, detail="ابتدا حداقل یک کالا به فهرست اضافه کنید.")

    with _job_lock:
        if _job["status"] == "running":
            raise HTTPException(status_code=409, detail="یک بررسی در حال اجراست.")
        _job.update({
            "status": "running",
            "completed": 0,
            "total": len(dataframe),
            "progress": 0,
            "message": "بررسی قیمت‌ها شروع شد",
            "rows": [
                {**{str(k): _safe_value(v) for k, v in row.items()}, "status": "PENDING", "price": None, "total_price": None, "error": None}
                for row in dataframe.to_dict(orient="records")
            ],
            "summary": None,
            "error": None,
        })

    worker = threading.Thread(
        target=_run_worker,
        args=(payload.workers, payload.timeout),
        name="price-monitor-web-worker",
        daemon=True,
    )
    worker.start()
    return {"ok": True, "message": "بررسی قیمت‌ها شروع شد."}


@app.get("/api/status")
async def get_status() -> dict[str, Any]:
    return _snapshot_job()


@app.get("/api/last-results")
async def get_last_results() -> dict[str, Any]:
    """Restore the most recent report in the dashboard after a server restart."""
    if not OUTPUT_FILE.exists():
        return {"rows": [], "summary": None}
    try:
        dataframe = pd.read_excel(OUTPUT_FILE)
        required = {"Status", "Price", "Total Price"}
        if not required.issubset(dataframe.columns):
            return {"rows": [], "summary": None}
        valid = dataframe[dataframe["Status"].isin(["OK", "NO", "ERROR"])]
        rows = [
            {
                "status": _safe_value(row.get("Status")),
                "price": _safe_value(row.get("Price")),
                "total_price": _safe_value(row.get("Total Price")),
            }
            for row in valid.to_dict(orient="records")
        ]
        summary = {
            "total_records": len(rows),
            "successful": sum(row["status"] == "OK" for row in rows),
            "not_found": sum(row["status"] == "NO" for row in rows),
            "errors": sum(row["status"] == "ERROR" for row in rows),
            "grand_total": sum(
                int(row["total_price"]) for row in rows
                if isinstance(row["total_price"], (int, float))
            ),
        }
        return {"rows": rows, "summary": summary}
    except Exception as exc:
        logger.warning("Unable to restore previous report: %s", exc)
        return {"rows": [], "summary": None, "error": str(exc)}


@app.get("/api/history")
async def get_history() -> dict[str, Any]:
    if not HISTORY_FILE.exists():
        return {"rows": []}
    try:
        dataframe = pd.read_excel(HISTORY_FILE)
        records = [
            {str(k): _safe_value(v) for k, v in row.items()}
            for row in dataframe.tail(30).to_dict(orient="records")
        ]
        records.reverse()
        return {"rows": records}
    except Exception as exc:
        logger.warning("Unable to read price history: %s", exc)
        return {"rows": [], "error": str(exc)}


@app.get("/api/download/{kind}")
async def download_file(kind: str) -> FileResponse:
    files = {
        "database": (DATABASE_FILE, "database.xlsx"),
        "output": (OUTPUT_FILE, "output.xlsx"),
        "history": (HISTORY_FILE, "price_history.xlsx"),
    }
    if kind not in files:
        raise HTTPException(status_code=404, detail="فایل درخواستی شناخته نشد.")
    path, filename = files[kind]
    if not path.exists():
        raise HTTPException(status_code=404, detail="هنوز فایلی برای دانلود وجود ندارد.")
    return FileResponse(path, filename=filename)


@app.get("/api/template")
async def download_template() -> StreamingResponse:
    buffer = BytesIO()
    pd.DataFrame(columns=["Supplier", "Quantity"]).to_excel(buffer, index=False)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="price-monitor-template.xlsx"'},
    )


def run_server(host: str = "127.0.0.1", port: int = 8000, *, open_browser: bool = False) -> None:
    """Start the local dashboard; optionally open it in the default browser."""
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - depends on optional web extras
        raise RuntimeError(
            "Web dashboard dependencies are missing. Install them with: "
            "python -m pip install -r requirements.txt"
        ) from exc

    address = f"http://{host}:{port}"
    print(f"\nDashboard available at {address}\nPress Ctrl+C to stop.\n", flush=True)
    if open_browser:
        Timer(1.2, lambda: webbrowser.open(address, new=2)).start()
    uvicorn.run(app, host=host, port=port, log_level="info")
