from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.core.exceptions import ValidationError
from app.models.output_job import OutputJob
from app.models.product import Product
from app.models.store import Store


def validate_known_keys(configuration: dict[str, Any], schema: dict[str, type]) -> None:
    """Shared validate_configuration() helper: configuration must be a dict,
    every key must be one of `schema`'s, and each present value must match
    its declared type. Keeps each concrete adapter's validation to a
    one-line schema declaration instead of repeating this logic.
    """
    if not isinstance(configuration, dict):
        raise ValidationError("configuration must be a JSON object.")
    unknown = set(configuration) - set(schema)
    if unknown:
        raise ValidationError(f"Unknown configuration key(s): {', '.join(sorted(unknown))}.")
    for key, expected_type in schema.items():
        if key in configuration and not isinstance(configuration[key], expected_type):
            names = (
                expected_type.__name__
                if isinstance(expected_type, type)
                else " or ".join(t.__name__ for t in expected_type)
            )
            raise ValidationError(f"configuration.{key} must be of type {names}.")


@dataclass
class OutputRenderContext:
    """Everything an adapter needs to render a payload for one product,
    resolved by the caller (output_job_service) before handing off — an
    adapter never queries the database directly.
    """

    product: Product
    store: Store | None
    price: Decimal
    currency: str
    public_url: str
    configuration: dict[str, Any]
    base_price: Decimal | None = None
    stock_qty: int | None = None
    # Stage 2: resolved visual template overrides (from LabelTemplate),
    # exactly what a later template-builder stage would extend with
    # fonts/layout/spacing — always optional fields, never DB access.
    template_colors: dict[str, str] | None = None
    template_background_image_url: str | None = None


class OutputAdapter(ABC):
    """Rule: every output type (ESL simulator, QR, PDF, web display, and any
    future real ESL vendor) implements this interface, so
    output_job_service never depends on a specific output type — same
    pattern as app/integrations/base.py's IntegrationAdapter.
    """

    @abstractmethod
    def validate_configuration(self, configuration: dict[str, Any]) -> None:
        """Raises app.core.exceptions.ValidationError if configuration is
        not valid for this output type. Called on output channel create/update.
        """
        ...

    @abstractmethod
    def render_payload(self, context: OutputRenderContext) -> dict[str, Any]:
        """Builds the base payload describing what should be shown/sent —
        the "what", before send_update() decides "how" (e.g. renders it
        into an image or a PDF).
        """
        ...

    @abstractmethod
    def send_update(
        self, *, job: OutputJob, context: OutputRenderContext, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Performs (or simulates) delivering the payload, returning the
        final payload to persist on OutputJob.payload — e.g. with a
        generated image attached. Real ESL vendor hardware/MQTT delivery is
        out of scope for this phase; this simulates or self-serves instead.
        """
        ...

    @abstractmethod
    def get_status(self, job: OutputJob) -> str:
        """Returns this output's current delivery status. With no external
        vendor/hardware integrated yet, every adapter reports the job's own
        stored status — this hook exists so a future real vendor adapter can
        poll the vendor's API instead.
        """
        ...
