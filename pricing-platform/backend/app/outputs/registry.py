from app.models.output_channel import OutputType
from app.outputs.base import OutputAdapter
from app.outputs.digital_signage import DigitalSignageAdapter
from app.outputs.ecommerce_integration import EcommerceIntegrationAdapter
from app.outputs.esl_simulator import ESLSimulatorAdapter
from app.outputs.pdf_label import PDFLabelAdapter
from app.outputs.pos_integration import POSIntegrationAdapter
from app.outputs.qr_code import QRCodeAdapter
from app.outputs.web_display import WebDisplayAdapter

_ADAPTERS: dict[OutputType, OutputAdapter] = {
    OutputType.ESL_SIMULATOR: ESLSimulatorAdapter(),
    OutputType.QR_CODE: QRCodeAdapter(),
    OutputType.PDF_LABEL: PDFLabelAdapter(),
    OutputType.WEB_DISPLAY: WebDisplayAdapter(),
    OutputType.POS_INTEGRATION: POSIntegrationAdapter(),
    OutputType.ECOMMERCE_INTEGRATION: EcommerceIntegrationAdapter(),
    OutputType.DIGITAL_SIGNAGE: DigitalSignageAdapter(),
}


def get_output_adapter(output_type: OutputType) -> OutputAdapter:
    return _ADAPTERS[output_type]
