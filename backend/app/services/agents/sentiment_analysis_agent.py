import re
from typing import List, Tuple
from app.schemas.agent_outputs import SentimentAnalysisOutput
from app.schemas.market_data import StockMarketData

# Financial Domain Lexicon for Rule-based Lexical Sentiment Scoring
POSITIVE_KEYWORDS = {
    "growth", "record", "beat", "surge", "gain", "profit", "expansion", "bullish",
    "upgrade", "breakout", "rally", "innovation", "outperform", "milestone", "dividend",
    "buyback", "partnership", "strong", "higher", "positive", "success", "leader",
}

NEGATIVE_KEYWORDS = {
    "loss", "fall", "drop", "plunge", "decline", "bearish", "downgrade", "probe",
    "investigation", "lawsuit", "cut", "warning", "miss", "weak", "slump", "fraud",
    "recession", "layoff", "debt", "risk", "struggle", "disappoint", "headwind",
}


class SentimentAnalysisAgent:
    """
    Specialist Agent responsible for financial news sentiment analysis,
    emerging corporate narrative tracking, and catalyst detection.
    """
    AGENT_NAME = "News & Market Sentiment Analyst"

    @classmethod
    def _score_headline(cls, text: str) -> float:
        """Scores a single headline or summary using financial keyword sentiment density."""
        if not text:
            return 0.0

        words = re.findall(r"\b[a-z]+\b", text.lower())
        if not words:
            return 0.0

        pos_count = sum(1 for w in words if w in POSITIVE_KEYWORDS)
        neg_count = sum(1 for w in words if w in NEGATIVE_KEYWORDS)

        total_matches = pos_count + neg_count
        if total_matches == 0:
            return 0.0

        return (pos_count - neg_count) / total_matches

    @classmethod
    def analyze(cls, data: StockMarketData) -> SentimentAnalysisOutput:
        ticker = data.ticker
        articles = data.news or []

        key_findings: List[str] = []
        warnings: List[str] = []
        positive_catalysts: List[str] = []
        negative_concerns: List[str] = []

        if not articles:
            return SentimentAnalysisOutput(
                agent_name=cls.AGENT_NAME,
                sentiment_score=0.0,
                sentiment_label="NEUTRAL",
                news_sample_size=0,
                analysis=f"No recent news articles were returned for {ticker} by the market data provider.",
                key_findings=["No recent news headlines available to evaluate market sentiment."],
                supporting_data={"news_count": 0, "positive_count": 0, "negative_count": 0},
                warnings_and_limitations=["Sentiment analysis is limited by the absence of fresh news items."],
                confidence_level=0.30,
            )

        scores: List[float] = []
        for article in articles:
            title = article.title or ""
            summary = article.summary or ""
            combined_text = f"{title} {summary}"

            score = cls._score_headline(combined_text)
            scores.append(score)

            if score > 0.15:
                positive_catalysts.append(title)
            elif score < -0.15:
                negative_concerns.append(title)

        # Average sentiment score
        avg_score = sum(scores) / len(scores) if scores else 0.0
        normalized_score = round(max(-1.0, min(1.0, avg_score)), 2)

        # Sentiment Category Label
        if normalized_score >= 0.40:
            sentiment_label = "VERY_BULLISH"
        elif normalized_score >= 0.10:
            sentiment_label = "BULLISH"
        elif normalized_score <= -0.40:
            sentiment_label = "VERY_BEARISH"
        elif normalized_score <= -0.10:
            sentiment_label = "BEARISH"
        else:
            sentiment_label = "NEUTRAL"

        key_findings.append(f"Evaluated {len(articles)} recent news articles, arriving at a {sentiment_label.replace('_', ' ').lower()} sentiment rating (Score: {normalized_score:+.2f}).")

        if positive_catalysts:
            key_findings.append(f"Identified {len(positive_catalysts)} constructive headlines highlighting operational and commercial catalysts.")
        if negative_concerns:
            key_findings.append(f"Identified {len(negative_concerns)} risk-related headlines noting operational, competitive, or macroeconomic hurdles.")

        if len(articles) < 5:
            warnings.append(f"Small news sample size ({len(articles)} articles) may reduce narrative sentiment reliability.")
            confidence = 0.65
        else:
            confidence = 0.85

        narrative = (
            f"Sentiment coverage for {ticker} reflects a {sentiment_label.replace('_', ' ').lower()} narrative "
            f"across {len(articles)} tracked news articles with an aggregate score of {normalized_score:+.2f}. "
            f"Positive catalysts lead by {len(positive_catalysts)} items vs {len(negative_concerns)} risk factors."
        )

        supporting_data = {
            "news_count": len(articles),
            "raw_average_score": normalized_score,
            "positive_headlines_count": len(positive_catalysts),
            "negative_headlines_count": len(negative_concerns),
            "latest_headline": articles[0].title if articles else None,
        }

        return SentimentAnalysisOutput(
            agent_name=cls.AGENT_NAME,
            sentiment_score=normalized_score,
            sentiment_label=sentiment_label,
            news_sample_size=len(articles),
            positive_catalysts=positive_catalysts[:5],
            negative_concerns=negative_concerns[:5],
            analysis=narrative,
            key_findings=key_findings,
            supporting_data=supporting_data,
            warnings_and_limitations=warnings,
            confidence_level=confidence,
        )

