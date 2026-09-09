from .hub import hub_mcp
from ..services.filemaker import list_layouts, find_records

@hub_mcp.tool()
def read_layout() -> dict:
    """Read all layout's name from FileMaker database.

    """
    layouts = list_layouts()
    return layouts

@hub_mcp.tool()
def read_record(layout: str, query: list[dict]) -> list[dict]:
    """Find records from FileMaker database.

    Available layouts and fields( layout:fields ):
    - Layout_A: Field_C, Field_I, Field_K, Field_L, Field_G, Field_H
    - Layout_B: Field_D, Field_F, Field_G, Field_H, Field_B
    - Layout_C: Field_D, Field_F, Field_G, Field_H, Field_B
    - Layout_D: Field_D, Field_F, Field_M, Field_B
    - Layout_E: Field_E, Field_N, Field_J, Field_A

    Query example:
        [{"Field_C": "06/01/2026...06/30/2026"}]
        [{"Field_C": "08/25/2026..."}]
        [{"Field_C": "...08/25/2026"}]
        [{"Field_I": "Media_A", "Field_L": "Value_A"}]
    """

    records = find_records(layout=layout, query=query)
    return records["response"]["data"]
