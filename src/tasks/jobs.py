"""Celery task definitions for Polylog6."""
from __future__ import annotations

from typing import Dict

from common.logging_setup import ensure_logging_initialised, get_logger
from tasks.celery_app import app

ensure_logging_initialised()
LOGGER = get_logger(__name__)


@app.task(name="polylog6.run_stability_analysis")
def run_stability_analysis(assembly_data: Dict, config: Dict | None = None) -> Dict:
    """Run a stability analysis asynchronously.

    Parameters
    ----------
    assembly_data:
        Serialized representation of the assembly.
    config:
        Optional configuration for the stability analyzer.
    """

    LOGGER.info("Received stability analysis task")

    # Lazy import to avoid Celery worker import cost when unused
    from src.engines.stability_analyzer import StabilityAnalyzer

    analyzer = StabilityAnalyzer(config=config)
    result = analyzer.calculate_stability(assembly_data)

    LOGGER.info("Completed stability analysis: %.3f", result)
    return {"stability_score": result}


@app.task(name="polylog6.generate_performance_report")
def generate_performance_report(report_context: Dict) -> Dict:
    """Generate a performance/KPI report asynchronously."""

    LOGGER.info("Generating performance report", extra={"context": report_context})

    # Example: placeholder for real implementation
    report = {
        "summary": "Performance report generated.",
        "context": report_context,
    }

    LOGGER.info("Performance report ready")
    return report
