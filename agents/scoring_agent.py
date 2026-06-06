class ScoringAgent:
    
    def calculate(
        self,
        fundamental_score,
        technical_score,
        news_score
    ):

        final_score = (

            fundamental_score * 0.5 +

            technical_score * 0.3 +

            news_score * 0.2

        )

        return round(
            final_score,
            2
        )