from config.logging_config import get_logger

logger = get_logger(__name__)


class ScoringAgent:

    def calculate(

        self,

        fundamental_score,

        technical_score,

        news_score

    ):

        logger.debug(

            f"Calculating final score - "
            f"Fundamental: {fundamental_score}, "
            f"Technical: {technical_score}, "
            f"News: {news_score}"

        )

        final_score = (

            fundamental_score * 0.60 +

            technical_score * 0.25 +

            news_score * 0.15

        )

        final_score = round(
            final_score,
            2
        )

        logger.info(
            f"Final score calculated: "
            f"{final_score}"
        )

        return final_score