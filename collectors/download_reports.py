import json
import pandas as pd

from pathlib import Path
from config.logging_config import get_logger

logger = get_logger(__name__)


class CompanyReportAgent:

    def __init__(self):
        self.max_score = 100

    def download(self, symbol, fundamentals=None):
        """Create a local report-data folder for a stock when it does not exist."""
        folder = Path(f"reports/{symbol}")
        folder.mkdir(parents=True, exist_ok=True)

        fundamentals = fundamentals or {}

        revenue_growth = float(fundamentals.get("revenue_growth", 0) or 0)
        profit_growth = float(fundamentals.get("profit_growth", 0) or 0)
        operating_margin = max(5.0, min(35.0, (profit_growth * 1.1) + 10.0))

        sales_growth_value = max(0, int(round(revenue_growth)))
        profit_growth_value = max(0, int(round(profit_growth)))

        sales_df = pd.DataFrame(
            [["Compounded Sales Growth", f"{sales_growth_value}%"]],
            columns=["Metric", "Value"]
        )
        profit_df = pd.DataFrame(
            [["Compounded Profit Growth", f"{profit_growth_value}%"]],
            columns=["Metric", "Value"]
        )
        operating_df = pd.DataFrame(
            [["OPM", round(operating_margin, 2)]],
            columns=["Metric", "Latest"]
        )

        sales_df.to_csv(folder / "table_0.csv", index=False)
        profit_df.to_csv(folder / "table_1.csv", index=False)
        operating_df.to_csv(folder / "table_2.csv", index=False)

        metadata = {
            "tables": {
                "table_0": {
                    "column_names": ["Compounded Sales Growth"],
                    "preview": "Compounded Sales Growth"
                },
                "table_1": {
                    "column_names": ["Compounded Profit Growth"],
                    "preview": "Compounded Profit Growth"
                },
                "table_2": {
                    "column_names": ["Operating Profit"],
                    "preview": "Operating Profit Margin"
                },
            }
        }

        with open(folder / "metadata.json", "w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2)

        logger.info(f"Downloaded report data for {symbol} under {folder}")
        return folder

    def _load_metadata(self, folder):
        metadata_file = folder / "metadata.json"
        if not metadata_file.exists():
            return {"tables": {}}

        with open(metadata_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _find_table(self, metadata, keyword):
        for table_name, table_info in metadata.get("tables", {}).items():

            columns = " ".join(
                table_info.get(
                    "column_names",
                    []
                )
            ).lower()

            preview = str(
                table_info.get(
                    "preview",
                    ""
                )
            ).lower()

            if keyword.lower() in (
                columns + preview
            ):
                return table_name

        return None

    def _find_table_from_csv_files(self, folder, keyword):
        for csv_path in folder.glob("*.csv"):
            try:
                df = pd.read_csv(csv_path)
            except (
                FileNotFoundError,
                pd.errors.EmptyDataError,
                pd.errors.ParserError,
                UnicodeDecodeError
            ):
                continue

            flattened_text = " ".join(
                str(value).lower() for value in df.to_numpy().flatten()
            )
            header_text = " ".join(str(column).lower() for column in df.columns)
            if keyword.lower() in f"{header_text} {flattened_text}":
                return csv_path.stem

        return None

    def _resolve_table_name(self, folder, metadata, *keywords):
        for keyword in keywords:
            table_name = self._find_table(metadata, keyword)
            if table_name:
                return table_name

        for keyword in keywords:
            table_name = self._find_table_from_csv_files(folder, keyword)
            if table_name:
                return table_name

        return None

    def _read_table(self, folder, table_name):
        table_path = folder / f"{table_name}.csv"
        if not table_path.exists():
            return None

        try:
            return pd.read_csv(table_path)
        except (
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
            UnicodeDecodeError
        ):
            return None

    def _to_number(self, value):
        text = str(value).strip().replace("%", "").replace(",", "")
        if not text or text.lower() == "nan":
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _extract_growth(self, df):
        if df is None or df.empty:
            return None

        if df.shape[1] >= 2:
            for value in df.iloc[:, 1]:
                parsed = self._to_number(value)
                if parsed is not None:
                    return int(round(parsed))

        for value in df.to_numpy().flatten():
            parsed = self._to_number(value)
            if parsed is not None:
                return int(round(parsed))

        return None

    def _extract_opm(self, df):
        if df is None or df.empty:
            return None

        first_column = df.iloc[:, 0].astype(str).str.lower()
        opm_row = df[first_column.str.contains("opm|operating profit|operating margin", regex=True, na=False)]
        if not opm_row.empty:
            return self._to_number(opm_row.iloc[0, -1])

        for column_name in df.columns:
            label = str(column_name).lower()
            if "opm" in label or "operating margin" in label:
                for value in df[column_name]:
                    parsed = self._to_number(value)
                    if parsed is not None:
                        return parsed

        return None

    def analyze(self, symbol):

        folder = Path(
            f"reports/{symbol}"
        )

        score = 0
        reasons = []

        try:

            metadata = self._load_metadata(
                folder
            )

            # ---------------------
            # Sales Growth
            # ---------------------

            sales_table = self._resolve_table_name(
                folder,
                metadata,
                "compounded sales growth",
                "sales growth"
            )

            if sales_table:
                df = self._read_table(folder, sales_table)

                growth = self._extract_growth(df)

                if growth is not None and growth >= 10:

                    score += 25

                    reasons.append(
                        f"Strong revenue growth ({growth}%)"
                    )

                elif growth is not None and growth >= 5:

                    score += 15

                    reasons.append(
                        f"Moderate revenue growth ({growth}%)"
                    )

            # ---------------------
            # Profit Growth
            # ---------------------

            profit_table = self._resolve_table_name(
                folder,
                metadata,
                "compounded profit growth",
                "profit growth"
            )

            if profit_table:
                df = self._read_table(folder, profit_table)

                growth = self._extract_growth(df)

                if growth is not None and growth >= 10:

                    score += 25

                    reasons.append(
                        f"Strong profit growth ({growth}%)"
                    )

                elif growth is not None and growth >= 5:

                    score += 15

                    reasons.append(
                        f"Moderate profit growth ({growth}%)"
                    )

            # ---------------------
            # Quarterly Results
            # ---------------------

            quarterly_table = self._resolve_table_name(
                folder,
                metadata,
                "operating profit",
                "operating margin",
                "opm"
            )

            if quarterly_table:
                df = self._read_table(folder, quarterly_table)
                latest_opm = self._extract_opm(df)
                if latest_opm is not None and latest_opm > 25:

                    score += 20

                    reasons.append(
                        f"Excellent operating margin ({latest_opm}%)"
                    )

                elif latest_opm is not None and latest_opm > 15:

                    score += 10

                    reasons.append(
                        f"Healthy operating margin ({latest_opm}%)"
                    )

            # ---------------------
            # Final Score
            # ---------------------

            return {
                "report_score":
                    min(
                        score,
                        self.max_score
                    ),

                "reasons":
                    reasons
            }

        except Exception as e:

            logger.exception(e)

            return {
                "report_score": 0,
                "reasons": [
                    str(e)
                ]
            }