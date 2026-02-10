import os

import joblib
from huggingface_hub import hf_hub_download

from metamaska.utils import remove_new_line, remove_whitespace, unquote

DEFAULT_LOCATION = os.path.join(os.path.dirname(__file__), 'models', 'payload_clf.joblib')
HF_REPO_ID = "happyhackingspace/metamaska"
HF_FILENAME = "models/payload_clf.joblib"


def _ensure_model(path):
    if not path:
        raise ValueError("payload clf model file doesn't exist")
    if os.path.isfile(path):
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return hf_hub_download(repo_id=HF_REPO_ID, filename=HF_FILENAME, local_dir=os.path.dirname(os.path.dirname(path)))


class PayloadClassifier:
    def __init__(self, payload_clf_filename=DEFAULT_LOCATION):
        model_path = _ensure_model(payload_clf_filename)
        self.payload_clf = joblib.load(model_path)
        self.classes_ = self.payload_clf.classes_

    def _transform(self, payload):
        if not payload:
            raise ValueError("payload is required.")

        payload = unquote(payload)
        payload = remove_new_line(payload)
        payload = payload.lower()
        payload = remove_whitespace(payload)

        return payload

    def predict(self, payload):
        payload = self._transform(payload)
        return self.payload_clf.predict([payload])

    def predict_proba(self, payload):
        payload = self._transform(payload)
        return self.payload_clf.predict_proba([payload])
