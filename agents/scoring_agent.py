from config.logging_config import get_logger

logger = get_logger(__name__)


class ScoringAgent:

    def preliminary_score(
        self,
        fundamental_score,
        technical_score
    ):

        return round(
            fundamental_score * 0.70 +
            technical_score * 0.30,
            2
        )

    def calculate(
        self,
        fundamental_score,
        technical_score,
        news_score,
        report_score,
        risk_score
    ):

        logger.debug(
            f"Calculating final score - "
            f"Fundamental: {fundamental_score}, "
            f"Technical: {technical_score}, "
            f"News: {news_score}, "
            f"Report: {report_score}, "
            f"Risk: {risk_score}"
        )

        final_score = (
            fundamental_score * 0.25 +
            technical_score * 0.15 +
            news_score * 0.15 +
            report_score * 0.30 +
            risk_score * 0.15
        )

        final_score = round(
            final_score,
            2
        )

        logger.info(
            f"Final score calculated: {final_score}"
        )

        return final_score