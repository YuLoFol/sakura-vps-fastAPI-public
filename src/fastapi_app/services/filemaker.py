"""
FileMaker Data API 共通 CRUD wrapper

底層的認證與請求處理委派給 filemaker_data_api._request 處理。
"""

from typing import Optional
from .filemaker_data_api import _request


def list_layouts(database: Optional[str] = None) -> dict:
    return _request(
        "GET",
        "/layouts",
        database=database
    )


def find_records(layout: str, query: list[dict], database: Optional[str] = None) -> dict:
    return _request(
        "POST",
        f"/layouts/{layout}/_find",
        database=database,
        json={"query": query}
    )


def create_record(layout: str, field_data: dict, database: Optional[str] = None) -> dict:
    return _request(
        "POST",
        f"/layouts/{layout}/records",
        database=database,
        json={"fieldData": field_data},
    )


def edit_record(
    layout: str, record_id: int, field_data: dict, database: Optional[str] = None
) -> dict:
    return _request(
        "PATCH",
        f"/layouts/{layout}/records/{record_id}",
        database=database,
        json={"fieldData": field_data},
    )


def delete_record(layout: str, record_id: int, database: Optional[str] = None) -> dict:
    return _request(
        "DELETE",
        f"/layouts/{layout}/records/{record_id}",
        database=database
    )


def run_script(
    layout: str, script_name: str, param: Optional[str] = None, database: Optional[str] = None
) -> dict:
    path = f"/layouts/{layout}/script/{script_name}"
    if param is not None:
        path += f"?script.param={param}"
    return _request("GET", path, database=database)