# tests/test_classifier.py
from unittest.mock import MagicMock, patch

from ml_pipeline.classifier import PolicyClassifier


def _mock_pipeline(labels, scores):
    pipe = MagicMock()
    pipe.return_value = {"labels": labels, "scores": scores}
    return pipe


@patch("ml_pipeline.classifier.pipeline")
def test_classify_risk_level_high(mock_pipeline_fn):
    mock_pipeline_fn.return_value = _mock_pipeline(
        ["high risk — mandatory compliance with penalties"],
        [0.92],
    )
    clf = PolicyClassifier()
    result = clf.classify_risk_level("Mandatory fines for non-compliance.")
    assert result["level"] == "high"
    assert result["score"] == 0.92


@patch("ml_pipeline.classifier.pipeline")
def test_classify_jurisdiction_maps_to_eu(mock_pipeline_fn):
    mock_pipeline_fn.return_value = _mock_pipeline(
        ["European Union policy"],
        [0.88],
    )
    clf = PolicyClassifier()
    result = clf.classify_jurisdiction("GDPR and AI Act requirements.")
    assert result["label"] == "EU"


@patch("ml_pipeline.classifier.pipeline")
def test_classify_full_returns_all_fields(mock_pipeline_fn):
    mock_pipeline_fn.return_value = _mock_pipeline(
        ["binding regulation"],
        [0.9],
    )
    clf = PolicyClassifier()
    # classify_full calls pipeline three times with different label sets
    clf.classifier = MagicMock(side_effect=[
        {"labels": ["binding regulation"], "scores": [0.9]},
        {"labels": ["high risk — mandatory compliance with penalties"], "scores": [0.85]},
        {"labels": ["United States policy"], "scores": [0.8]},
    ])
    result = clf.classify_full("AI compliance text", title="Federal rule")
    assert result["doc_type"] == "binding regulation"
    assert result["risk_level"] == "high"
    assert result["jurisdiction"] == "US"
