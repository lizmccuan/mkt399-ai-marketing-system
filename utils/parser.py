"""Parser utilities for handling GA4 and GSC CSV data."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd


GA4_SHARED_METRIC_COLUMNS = [
    "new_users",
    "active_users",
    "returning_users",
    "total_users",
    "sessions",
    "engagement_rate",
    "average_engagement_time_per_session",
]

GA4_HEADER_ALIASES = {
    "page title": "page_title",
    "page_title": "page_title",
    "page title and screen class": "page_title",
    "session source / medium": "session_source_/_medium",
    "session source/medium": "session_source_/_medium",
    "session_source_/_medium": "session_source_/_medium",
    "session_source_medium": "session_source_/_medium",
    "new users": "new_users",
    "new_users": "new_users",
    "active users": "active_users",
    "active_users": "active_users",
    "returning users": "returning_users",
    "returning_users": "returning_users",
    "total users": "total_users",
    "total_users": "total_users",
    "sessions": "sessions",
    "engagement rate": "engagement_rate",
    "engagement_rate": "engagement_rate",
    "average engagement time per session": "average_engagement_time_per_session",
    "average_engagement_time_per_session": "average_engagement_time_per_session",
}

GA4_REPORT_CONFIGS = {
    "ga4_pages": {
        "expected_columns": ["page_title", *GA4_SHARED_METRIC_COLUMNS],
        "primary_dimension": "page_title",
    },
    "ga4_source": {
        "expected_columns": ["session_source_/_medium", *GA4_SHARED_METRIC_COLUMNS],
        "primary_dimension": "session_source_/_medium",
    },
}


def load_prompt(prompt_name: str) -> str:
    """Load prompt text from the prompts folder."""
    prompt_path = Path("prompts") / prompt_name

    if not prompt_path.exists():
        return f"Prompt file not found: {prompt_name}"

    return prompt_path.read_text(encoding="utf-8").strip()


def parse_uploaded_csv(file_obj: Any, source_name: str) -> pd.DataFrame:
    """Convert an uploaded Streamlit file into a pandas DataFrame."""
    if file_obj is None:
        return pd.DataFrame()

    text_data = file_obj.getvalue().decode("utf-8-sig")
    dataframe = parse_csv_text(text_data, source_name)
    return clean_marketing_dataframe(dataframe, source_name)


def parse_csv_file(file_path: str, source_name: str) -> pd.DataFrame:
    """Load a CSV file from disk and return a cleaned DataFrame."""
    text_data = Path(file_path).read_text(encoding="utf-8-sig")
    dataframe = parse_csv_text(text_data, source_name)
    return clean_marketing_dataframe(dataframe, source_name)


def parse_csv_text(text_data: str, source_name: str | None = None) -> pd.DataFrame:
    """Read CSV text safely for GA4 page, GA4 source, and GSC query exports."""
    lines = text_data.splitlines()

    ga4_report_key = get_ga4_report_key(source_name, lines)
    if ga4_report_key:
        return parse_ga4_text(text_data, ga4_report_key)

    cleaned_text = prepare_generic_text(lines)

    if not cleaned_text.strip():
        return pd.DataFrame()

    return pd.read_csv(
        StringIO(cleaned_text),
        skip_blank_lines=True,
        on_bad_lines="skip",
        engine="python",
    )


def parse_ga4_text(text_data: str, report_key: str) -> pd.DataFrame:
    """Parse GA4 exports with strict header detection and validation."""
    config = GA4_REPORT_CONFIGS[report_key]
    rows = list(csv.reader(StringIO(text_data)))
    header_index = find_ga4_header_index_from_rows(rows, config["expected_columns"])

    if header_index is None:
        print("[Parser Warning] Could not find the GA4 header row.")
        return pd.DataFrame(columns=config["expected_columns"])

    raw_header = rows[header_index]
    header_map = build_ga4_header_map(raw_header, config["expected_columns"])
    data_rows = collect_ga4_data_rows(rows[header_index + 1 :])
    dataframe = build_ga4_dataframe(data_rows, header_map, config["expected_columns"])

    if is_misaligned_ga4_dataframe(dataframe, config["primary_dimension"]):
        print("[Parser Warning] GA4 primary dimension looks numeric. Attempting column shift recovery.")
        dataframe = attempt_ga4_column_shifts(data_rows, config["expected_columns"], config["primary_dimension"])

    return dataframe


def prepare_generic_text(lines: list[str]) -> str:
    """Drop leading metadata lines and blank lines before the real header."""
    table_start_index = 0

    for index, line in enumerate(lines):
        stripped_line = line.strip()

        if stripped_line.startswith("#"):
            continue

        if not stripped_line:
            continue

        table_start_index = index
        break
    else:
        return ""

    return "\n".join(lines[table_start_index:])


def get_ga4_report_key(source_name: str | None, lines: list[str]) -> str | None:
    """Detect which GA4 report type an uploaded file matches."""
    normalized_source = source_name.strip().lower() if source_name else ""

    if normalized_source in {"ga4", "ga4_pages", "ga4_page_title_report"}:
        return "ga4_pages"

    if normalized_source in {"ga4_source", "ga4_session_source_medium", "ga4_source_medium"}:
        return "ga4_source"

    for report_key, config in GA4_REPORT_CONFIGS.items():
        if find_ga4_header_index(lines, config["expected_columns"]) is not None:
            return report_key

    return None


def find_ga4_header_index(lines: list[str], expected_columns: list[str]) -> int | None:
    """Find the GA4 header row from raw lines."""
    return find_ga4_header_index_from_rows(list(csv.reader(StringIO("\n".join(lines)))), expected_columns)


def find_ga4_header_index_from_rows(rows: list[list[str]], expected_columns: list[str]) -> int | None:
    """Find the GA4 header row from parsed CSV rows."""
    for index, row in enumerate(rows):
        canonical_row = [canonicalize_ga4_header(cell) for cell in row if str(cell).strip()]

        if canonical_row[: len(expected_columns)] == expected_columns:
            return index

    return None


def canonicalize_ga4_header(value: str) -> str:
    """Convert a raw GA4 header cell into a canonical name."""
    normalized = normalize_text(value)
    return GA4_HEADER_ALIASES.get(normalized, normalized.replace(" ", "_"))


def build_ga4_header_map(raw_header: list[str], expected_columns: list[str]) -> list[int]:
    """Map the expected GA4 columns to their positions in the raw header."""
    canonical_header = [canonicalize_ga4_header(cell) for cell in raw_header]
    header_map = []

    for column in expected_columns:
        header_map.append(canonical_header.index(column) if column in canonical_header else -1)

    return header_map


def collect_ga4_data_rows(rows: list[list[str]]) -> list[list[str]]:
    """Keep only usable GA4 rows after the header row."""
    cleaned_rows = []

    for row in rows:
        if not row:
            continue

        stripped_values = [str(cell).strip() for cell in row]

        if not any(stripped_values):
            continue

        if any(value.startswith("#") for value in stripped_values if value):
            continue

        if any("grand total" in value.lower() for value in stripped_values if value):
            continue

        cleaned_rows.append(stripped_values)

    return cleaned_rows


def build_ga4_dataframe(data_rows: list[list[str]], header_map: list[int], expected_columns: list[str]) -> pd.DataFrame:
    """Build a DataFrame from raw GA4 rows using detected header positions."""
    records = [extract_ga4_record(row, header_map, expected_columns) for row in data_rows]
    dataframe = pd.DataFrame(records, columns=expected_columns)
    return coerce_ga4_types(dataframe)


def extract_ga4_record(row: list[str], header_map: list[int], expected_columns: list[str]) -> dict[str, Any]:
    """Extract the expected GA4 columns from a raw row."""
    record = {}

    for column, index in zip(expected_columns, header_map):
        record[column] = row[index].strip() if 0 <= index < len(row) else ""

    return record


def attempt_ga4_column_shifts(
    data_rows: list[list[str]], expected_columns: list[str], primary_dimension: str
) -> pd.DataFrame:
    """Try shifting raw rows left and right when the first parse looks malformed."""
    best_dataframe = pd.DataFrame(columns=expected_columns)
    best_score = -1.0

    for shift in range(-2, 3):
        shifted_records = [build_shifted_ga4_record(row, shift, expected_columns) for row in data_rows]
        candidate = coerce_ga4_types(pd.DataFrame(shifted_records, columns=expected_columns))
        score = score_ga4_alignment(candidate, primary_dimension)

        if score > best_score:
            best_score = score
            best_dataframe = candidate

    return best_dataframe


def build_shifted_ga4_record(row: list[str], shift: int, expected_columns: list[str]) -> dict[str, Any]:
    """Build a record by shifting row values left or right."""
    record = {}

    for index, column in enumerate(expected_columns):
        source_index = index + shift
        record[column] = row[source_index].strip() if 0 <= source_index < len(row) else ""

    return record


def coerce_ga4_types(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Convert GA4 metric columns into consistent numeric types."""
    converted = dataframe.copy()

    for column in ["new_users", "active_users", "returning_users", "total_users", "sessions"]:
        converted[column] = pd.to_numeric(converted[column], errors="coerce")

    converted["engagement_rate"] = converted["engagement_rate"].apply(to_number)
    converted["average_engagement_time_per_session"] = converted[
        "average_engagement_time_per_session"
    ].apply(parse_duration_to_seconds)

    return converted


def is_misaligned_ga4_dataframe(dataframe: pd.DataFrame, primary_dimension: str) -> bool:
    """Check whether the parsed GA4 table still looks shifted."""
    if dataframe.empty:
        return False

    validation = validate_ga4_dataframe(dataframe, primary_dimension)
    return not validation["looks_valid"]


def score_ga4_alignment(dataframe: pd.DataFrame, primary_dimension: str) -> float:
    """Score whether parsed GA4 columns look correctly aligned."""
    if dataframe.empty:
        return 0.0

    dimension_values = dataframe[primary_dimension].dropna().astype(str).head(10).tolist()

    if not dimension_values:
        return 0.0

    text_ratio = sum(1 for value in dimension_values if value.strip() and not looks_numeric(value)) / len(dimension_values)
    sessions_ratio = dataframe["sessions"].notna().mean() if "sessions" in dataframe else 0.0
    engagement_ratio = dataframe["engagement_rate"].notna().mean() if "engagement_rate" in dataframe else 0.0
    average_time_ratio = (
        dataframe["average_engagement_time_per_session"].notna().mean()
        if "average_engagement_time_per_session" in dataframe
        else 0.0
    )

    return text_ratio + sessions_ratio + engagement_ratio + average_time_ratio


def clean_marketing_dataframe(dataframe: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """Apply a few beginner-friendly cleanup steps to marketing data."""
    cleaned = dataframe.copy()
    cleaned.columns = [normalize_column_name(column) for column in cleaned.columns]
    cleaned = cleaned.dropna(how="all")

    report_key = get_ga4_report_key(source_name, [])
    if report_key:
        cleaned = normalize_ga4_columns(cleaned)
        primary_dimension = GA4_REPORT_CONFIGS[report_key]["primary_dimension"]
        expected_columns = GA4_REPORT_CONFIGS[report_key]["expected_columns"]
        cleaned = recover_misaligned_ga4_dataframe(cleaned, expected_columns, primary_dimension)
        warn_if_misaligned_ga4(cleaned, primary_dimension)

    cleaned["data_source"] = source_name
    return cleaned


def normalize_ga4_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Rename common GA4 export columns into a consistent set."""
    renamed = dataframe.copy()
    column_map = {
        "page_title_and_screen_class": "page_title",
        "page_title": "page_title",
        "session_source_/_medium": "session_source_/_medium",
        "session_source_medium": "session_source_/_medium",
        "source_medium": "session_source_/_medium",
        "new_users": "new_users",
        "active_users": "active_users",
        "returning_users": "returning_users",
        "total_users": "total_users",
        "sessions": "sessions",
        "engagement_rate": "engagement_rate",
        "average_engagement_time_per_session": "average_engagement_time_per_session",
    }

    matching_columns = {column: column_map[column] for column in renamed.columns if column in column_map}
    return renamed.rename(columns=matching_columns)


def warn_if_misaligned_ga4(dataframe: pd.DataFrame, primary_dimension: str) -> None:
    """Print a warning when the main GA4 dimension values are mostly numeric."""
    if not validate_ga4_dataframe(dataframe, primary_dimension)["looks_valid"]:
        print(f"[Parser Warning] GA4 {primary_dimension} values are mostly numeric. The file may still be malformed.")


def recover_misaligned_ga4_dataframe(
    dataframe: pd.DataFrame, expected_columns: list[str], primary_dimension: str
) -> pd.DataFrame:
    """Try to recover a GA4 DataFrame when values appear shifted between columns."""
    if not set(expected_columns).issubset(dataframe.columns):
        return dataframe

    candidate = coerce_ga4_types(dataframe[expected_columns].copy())

    if not is_misaligned_ga4_dataframe(candidate, primary_dimension):
        return dataframe

    print("[Parser Warning] Attempting GA4 DataFrame realignment.")
    best_dataframe = candidate
    best_score = score_ga4_alignment(candidate, primary_dimension)

    for shift in range(-2, 3):
        shifted_records = []

        for _, row in candidate.iterrows():
            values = ["" if pd.isna(value) else str(value) for value in row.tolist()]
            shifted_records.append(build_shifted_ga4_record(values, shift, expected_columns))

        shifted_candidate = coerce_ga4_types(pd.DataFrame(shifted_records, columns=expected_columns))
        shifted_score = score_ga4_alignment(shifted_candidate, primary_dimension)

        if shifted_score > best_score:
            best_score = shifted_score
            best_dataframe = shifted_candidate

    recovered = dataframe.copy()

    for column in expected_columns:
        recovered[column] = best_dataframe[column]

    return recovered


def validate_ga4_dataframe(dataframe: pd.DataFrame, primary_dimension: str) -> dict[str, Any]:
    """Validate that parsed GA4 columns look correctly aligned."""
    if dataframe.empty or primary_dimension not in dataframe.columns:
        return {
            "dimension_text_ratio": 0.0,
            "sessions_numeric_ratio": 0.0,
            "engagement_rate_numeric_ratio": 0.0,
            "average_time_valid_ratio": 0.0,
            "looks_valid": False,
        }

    dimension_values = dataframe[primary_dimension].dropna().astype(str).head(10).tolist()
    dimension_text_ratio = (
        sum(1 for value in dimension_values if value.strip() and not looks_numeric(value)) / len(dimension_values)
        if dimension_values
        else 0.0
    )
    sessions_numeric_ratio = dataframe["sessions"].notna().mean() if "sessions" in dataframe else 0.0
    engagement_rate_numeric_ratio = dataframe["engagement_rate"].notna().mean() if "engagement_rate" in dataframe else 0.0
    average_time_valid_ratio = (
        dataframe["average_engagement_time_per_session"].apply(lambda value: value is None or pd.notna(value)).mean()
        if "average_engagement_time_per_session" in dataframe
        else 0.0
    )

    looks_valid = (
        dimension_text_ratio >= 0.6
        and sessions_numeric_ratio >= 0.8
        and engagement_rate_numeric_ratio >= 0.8
        and average_time_valid_ratio >= 0.8
    )

    return {
        "dimension_text_ratio": dimension_text_ratio,
        "sessions_numeric_ratio": sessions_numeric_ratio,
        "engagement_rate_numeric_ratio": engagement_rate_numeric_ratio,
        "average_time_valid_ratio": average_time_valid_ratio,
        "looks_valid": looks_valid,
    }


def normalize_column_name(column: Any) -> str:
    """Convert a column name into a simple snake_case label."""
    return normalize_text(str(column)).replace(" ", "_")


def normalize_text(value: str) -> str:
    """Normalize text for matching headers and column names."""
    return " ".join(value.strip().lower().replace("_", " ").split())


def looks_numeric(value: str) -> bool:
    """Check whether a text value is mostly numeric."""
    cleaned = value.replace(",", "").replace(".", "").strip()
    return cleaned.isdigit()


def parse_duration_to_seconds(value: Any) -> float | None:
    """Convert a GA4 time value like 00:01:24 into seconds."""
    if value in (None, ""):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text_value = str(value).strip()

    if looks_numeric(text_value):
        return float(text_value)

    parts = text_value.split(":")

    if len(parts) != 3:
        return None

    try:
        hours, minutes, seconds = [int(part) for part in parts]
    except ValueError:
        return None

    return float(hours * 3600 + minutes * 60 + seconds)


def to_number(value: Any) -> float | None:
    """Convert common CSV values to numbers when possible."""
    if value in (None, ""):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    cleaned = str(value).replace(",", "").replace("%", "").strip()

    try:
        return float(cleaned)
    except ValueError:
        return None


def summarize_dataframe(dataframe: pd.DataFrame, label: str) -> dict[str, Any]:
    """Build a compact summary of a DataFrame for the agents."""
    if dataframe.empty:
        return {
            "label": label,
            "rows": 0,
            "columns": [],
            "sample_records": [],
            "key_metrics": {},
        }

    numeric_columns = dataframe.select_dtypes(include="number").columns.tolist()
    key_metrics = {}

    for column in numeric_columns[:5]:
        key_metrics[column] = round(float(dataframe[column].fillna(0).sum()), 2)

    return {
        "label": label,
        "rows": int(len(dataframe)),
        "columns": list(dataframe.columns),
        "sample_records": dataframe.head(5).fillna("").to_dict(orient="records"),
        "key_metrics": key_metrics,
    }
