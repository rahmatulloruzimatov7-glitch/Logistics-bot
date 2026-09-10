"""Google Sheets — read Malumotnoma and write to Reyslar sheet."""
import asyncio
import json
import logging
import os
import time
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

CREDENTIALS_PATH = Path(__file__).resolve().parent.parent / "credentials" / "service_account.json"

MALUMOTNOMA_SHEET = "Malumotnoma"
REYSLAR_SHEET = "Reyslar"

COL_TV_DAVLAT_RAQAMI = 1
COL_HAYDOVCHI = 2
COL_TRANSPORT_TURI = 3
COL_PUNKTLAR = 7
COL_MIJOZLAR = 8
COL_SHARTNOMA = 10


def _get_client() -> gspread.Client:
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        creds = Credentials.from_service_account_info(
            json.loads(sa_json), scopes=SCOPES
        )
    else:
        creds = Credentials.from_service_account_file(
            str(CREDENTIALS_PATH), scopes=SCOPES
        )
    return gspread.authorize(creds)


def _retry(fn, retries: int = 3, delay: float = 2.0):
    for attempt in range(retries):
        try:
            return fn()
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429 and attempt < retries - 1:
                logger.warning("Sheets API rate limit hit, retrying in %ss...", delay)
                time.sleep(delay)
                delay *= 2
            else:
                raise


async def get_malumotnoma_data(sheet_id: str) -> dict:
    def _read():
        client = _get_client()
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.worksheet(MALUMOTNOMA_SHEET)
        return sheet.get_all_values()

    rows = await asyncio.to_thread(lambda: _retry(_read))

    data = {
        "tv_davlat_raqamlari": [],
        "haydovchilar": [],
        "transport_turlari": [],
        "punktlar": [],
        "mijozlar": [],
        "shartnomalar": [],
    }

    for row in rows[1:]:
        def get_col(r, idx):
            return r[idx].strip() if idx < len(r) else ""

        tv = get_col(row, COL_TV_DAVLAT_RAQAMI)
        haydovchi = get_col(row, COL_HAYDOVCHI)
        transport = get_col(row, COL_TRANSPORT_TURI)
        punkt = get_col(row, COL_PUNKTLAR)
        mijoz = get_col(row, COL_MIJOZLAR)
        shartnoma = get_col(row, COL_SHARTNOMA)

        if tv:
            data["tv_davlat_raqamlari"].append(tv)
        if haydovchi:
            data["haydovchilar"].append(haydovchi)
        if transport:
            data["transport_turlari"].append(transport)
        if punkt:
            data["punktlar"].append(punkt)
        if mijoz:
            data["mijozlar"].append(mijoz)
        if shartnoma:
            data["shartnomalar"].append(shartnoma)

    return data


async def append_to_reyslar(sheet_id: str, extracted: dict) -> None:
    naqd = extracted.get("naqd_tushum", 0) or 0
    naqdsiz = extracted.get("naqdsiz_tushum", 0) or 0
    jami = extracted.get("jami_tushum", naqd + naqdsiz) or (naqd + naqdsiz)

    row = [
        extracted.get("sana", ""),
        extracted.get("reys_id", ""),
        extracted.get("jonatish_nuqtasi", ""),
        extracted.get("yetkazish_nuqtasi", ""),
        extracted.get("mijoz", ""),
        extracted.get("shartnoma_raqami", ""),
        extracted.get("yuk", ""),
        extracted.get("transport_turi", ""),
        extracted.get("tv_davlat_raqami", ""),
        extracted.get("haydovchi", ""),
        naqd,
        naqdsiz,
        jami,
    ]

        def _write():
        client = _get_client()
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.worksheet(REYSLAR_SHEET)

        # Find last row with data and write after it
        all_values = sheet.get_all_values()

        # Find last non-empty row
        last_row = 1
        for i, r in enumerate(all_values, start=1):
            if any(cell.strip() for cell in r):
                last_row = i

        next_row = last_row + 1

        sheet.update(
            f"A{next_row}",
            [row],
            value_input_option="USER_ENTERED"
        )

    await asyncio.to_thread(lambda: _retry(_write))
    logger.info("Written to row %s in Reyslar", extracted.get("reys_id"))
