from config.logging_config import get_logger

logger = get_logger(__name__)

class ScoringAgent:
    
    def calculate(
        self,
        fundamental_score,
        technical_score,
        news_score
    ):
        logger.debug(f"Calculating final score - Fundamental: {fundamental_score}, Technical: {technical_score}, News: {news_score}")

        final_score = (

            fundamental_score * 0.5 +

            technical_score * 0.3 +

            news_score * 0.2

        )

        final_score = round(final_score, 2)
        logger.info(f"Final score calculated: {final_score}")
        return final_score