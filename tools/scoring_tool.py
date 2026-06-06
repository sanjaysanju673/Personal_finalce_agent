from config.constants import *


def calculate_score(
    fundamental_score,
    technical_score,
    news_score
):

    return (
        fundamental_score * 0.5
        + technical_score * 0.3
        + news_score * 0.2
    )