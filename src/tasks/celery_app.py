"""Celery application setup for Polylog6."""
from __future__ import annotations

import os

from celery import Celery


def create_celery_app() -> Celery:
    """Instantiate and configure the Celery application."""

    broker_url = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
    result_backend = os.getenv("CELERY_RESULT_BACKEND", "rpc://")

    app = Celery(
        "polylog6",
        broker=broker_url,
        backend=result_backend,
        include=["tasks.jobs"],
    )

    app.conf.update(
        task_default_queue=os.getenv("CELERY_DEFAULT_QUEUE", "polylog6.default"),
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone=os.getenv("CELERY_TIMEZONE", "UTC"),
        enable_utc=True,
        worker_send_task_events=True,
        task_send_sent_event=True,
    )

    return app


app = create_celery_app()

__all__ = ["app", "create_celery_app"]
