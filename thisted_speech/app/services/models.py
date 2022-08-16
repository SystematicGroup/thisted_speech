from thisted_speech.app.payloads.totext import ToTextResult
from thisted_speech.models import totext_service
from thisted_speech.models.totext_service import CurrentStateModel


class ToTextModel:
    def __init__(self):
        self.current_state = CurrentStateModel()

    def get_next(self) -> ToTextResult:
        is_final, transcript = totext_service.get_next(self.current_state)
        return ToTextResult(is_final=is_final, transcript=transcript)
