"""
Business metrics for Jules application.

Tracks KPIs beyond technical metrics.
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import logging

logger = logging.getLogger(__name__)

# Recipe Extraction Metrics
recipes_extracted_total = Counter(
    'recipes_extracted_total',
    'Total recipes extracted',
    ['status', 'source']  # status: success/failed, source: handwritten/printed/url
)

recipe_extraction_confidence = Histogram(
    'recipe_extraction_confidence',
    'AI confidence scores for recipe extraction',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
)

recipe_extraction_duration_seconds = Histogram(
    'recipe_extraction_duration_seconds',
    'Time to extract recipe',
    buckets=[1, 5, 10, 20, 30, 60]
)

# Meal Planning Metrics
meal_plans_completed = Counter(
    'meal_plans_completed_total',
    'Weekly meal plans completed',
    ['household_tier']  # budget, mid, premium, organic
)

meal_planning_participation_rate = Gauge(
    'meal_planning_participation_rate',
    'Percentage of family members who voted',
    ['household_id']
)

# SMS Metrics
sms_opt_out_rate = Gauge(
    'sms_opt_out_rate',
    'Percentage of users who opted out'
)

sms_engagement_rate = Gauge(
    'sms_engagement_rate',
    'Percentage of users who respond to messages'
)

messages_per_household = Histogram(
    'messages_per_household_per_week',
    'SMS messages sent per household per week',
    buckets=[5, 10, 15, 20, 30, 50, 100]
)

# User Behavior Metrics
shopping_list_generated = Counter(
    'shopping_lists_generated_total',
    'Shopping lists generated',
    ['generation_method']  # manual, ai_suggested
)

pantry_scans_completed = Counter(
    'pantry_scans_completed_total',
    'Pantry scans completed',
    ['scan_type']  # full_pantry, fridge, freezer
)

# Retention Metrics
active_households = Gauge(
    'active_households',
    'Number of households with activity in last 7 days'
)

churn_rate = Gauge(
    'churn_rate',
    'Percentage of households that churned this month'
)

# Cost Metrics
ai_api_cost_dollars = Counter(
    'ai_api_cost_dollars',
    'Estimated AI API costs',
    ['provider']  # claude, openai
)

sms_cost_dollars = Counter(
    'sms_cost_dollars',
    'SMS messaging costs',
    ['provider']  # twilio, telnyx
)

# Feature Usage
feature_usage = Counter(
    'feature_usage_total',
    'Feature usage by users',
    ['feature']  # recipe_extraction, meal_planning, pantry_scan, etc.
)


class BusinessMetricsCollector:
    """Helper class for recording business metrics."""

    @staticmethod
    def record_recipe_extraction(
        status: str,
        source: str,
        confidence: float,
        duration_seconds: float,
        cost_dollars: float = 0
    ):
        """Record recipe extraction event."""
        recipes_extracted_total.labels(status=status, source=source).inc()

        if status == "success":
            recipe_extraction_confidence.observe(confidence)

        recipe_extraction_duration_seconds.observe(duration_seconds)

        if cost_dollars > 0:
            ai_api_cost_dollars.labels(provider="claude").inc(cost_dollars)

        logger.info("metric_recorded",
                   metric="recipe_extraction",
                   status=status,
                   confidence=confidence)

    @staticmethod
    def record_meal_plan_completion(household_tier: str, participation_rate: float):
        """Record meal plan completion."""
        meal_plans_completed.labels(household_tier=household_tier).inc()

        logger.info("metric_recorded",
                   metric="meal_plan_completed",
                   tier=household_tier,
                   participation=participation_rate)

    @staticmethod
    def record_sms_sent(household_id: str, cost_dollars: float):
        """Record SMS sent."""
        sms_cost_dollars.labels(provider="twilio").inc(cost_dollars)

        logger.info("metric_recorded",
                   metric="sms_sent",
                   household_id=household_id,
                   cost=cost_dollars)

    @staticmethod
    def record_opt_out(total_members: int, opted_out: int):
        """Update opt-out rate."""
        rate = (opted_out / total_members * 100) if total_members > 0 else 0
        sms_opt_out_rate.set(rate)

        logger.info("metric_recorded",
                   metric="opt_out_rate",
                   rate=rate)

    @staticmethod
    def record_feature_usage(feature: str):
        """Record feature usage."""
        feature_usage.labels(feature=feature).inc()
