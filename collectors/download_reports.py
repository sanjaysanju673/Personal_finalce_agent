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

        with open(
            metadata_file,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    def _find_table(self, metadata, keyword):

        for table_name, table_info in metadata[
            "tables"
        ].items():

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

            sales_table = self._find_table(
                metadata,
                "compounded sales growth"
            )

            if sales_table:

                df = pd.read_csv(
                    folder /
                    f"{sales_table}.csv"
                )

                growth = int(
                    str(
                        df.iloc[1, 1]
                    ).replace(
                        "%",
                        ""
                    )
                )

                if growth >= 10:

                    score += 25

                    reasons.append(
                        f"Strong revenue growth ({growth}%)"
                    )

                elif growth >= 5:

                    score += 15

                    reasons.append(
                        f"Moderate revenue growth ({growth}%)"
                    )

            # ---------------------
            # Profit Growth
            # ---------------------

            profit_table = self._find_table(
                metadata,
                "compounded profit growth"
            )

            if profit_table:

                df = pd.read_csv(
                    folder /
                    f"{profit_table}.csv"
                )

                growth = int(
                    str(
                        df.iloc[1, 1]
                    ).replace(
                        "%",
                        ""
                    )
                )

                if growth >= 10:

                    score += 25

                    reasons.append(
                        f"Strong profit growth ({growth}%)"
                    )

                elif growth >= 5:

                    score += 15

                    reasons.append(
                        f"Moderate profit growth ({growth}%)"
                    )

            # ---------------------
            # Quarterly Results
            # ---------------------

            quarterly_table = self._find_table(
                metadata,
                "operating profit"
            )

            if quarterly_table:

                df = pd.read_csv(
                    folder /
                    f"{quarterly_table}.csv"
                )

                try:

                    opm_row = df[
                        df.iloc[:, 0]
                        .astype(str)
                        .str.contains(
                            "OPM",
                            case=False,
                            na=False
                        )
                    ]

                    if not opm_row.empty:

                        latest_opm = str(
                            opm_row.iloc[
                                0, -1
                            ]
                        ).replace(
                            "%",
                            ""
                        )

                        latest_opm = float(
                            latest_opm
                        )

                        if latest_opm > 25:

                            score += 20

                            reasons.append(
                                f"Excellent operating margin ({latest_opm}%)"
                            )

                        elif latest_opm > 15:

                            score += 10

                            reasons.append(
                                f"Healthy operating margin ({latest_opm}%)"
                            )

                except Exception:
                    pass

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