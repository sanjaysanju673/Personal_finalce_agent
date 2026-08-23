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

    def dynamic_trade_score(
        self,
        momentum_score,
        relative_strength_score,
        volume_score,
        setup_score,
        market_regime_score,
        catalyst_score,
        risk_score
    ):
        """Compute the live trading score using the project’s weighted rules."""
        trade_score = (
            0.25 * momentum_score +
            0.20 * relative_strength_score +
            0.15 * volume_score +
            0.15 * setup_score +
            0.10 * market_regime_score +
            0.10 * catalyst_score +
            0.05 * risk_score
        )
        return round(trade_score, 2)

    def calculate(
        self,
        fundamental_score,
        technical_score,
        news_score,
        report_score,
        risk_score
    ):

        logger.debug(
            f"Calculating dynamic trade score - "
            f"Fundamental: {fundamental_score}, "
            f"Technical: {technical_score}, "
            f"News: {news_score}, "
            f"Report: {report_score}, "
            f"Risk: {risk_score}"
        )

        momentum_score = max(0, min(100, float(technical_score)))
        relative_strength_score = max(0, min(100, float(fundamental_score)))
        volume_score = max(0, min(100, ((float(technical_score) + float(news_score)) / 2.0)))
        setup_score = max(0, min(100, float(technical_score)))
        market_regime_score = max(0, min(100, ((float(technical_score) + float(news_score) + float(risk_score)) / 3.0)))
        catalyst_score = max(0, min(100, float(news_score)))

        trade_score = self.dynamic_trade_score(
            momentum_score=momentum_score,
            relative_strength_score=relative_strength_score,
            volume_score=volume_score,
            setup_score=setup_score,
            market_regime_score=market_regime_score,
            catalyst_score=catalyst_score,
            risk_score=max(0, min(100, float(risk_score)))
        )

        logger.info(
            f"Dynamic trade score calculated: {trade_score}"
        )

        return trade_score