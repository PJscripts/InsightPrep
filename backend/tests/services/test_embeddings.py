import logging

import pytest

from app.services.rag.embeddings import LocalSentenceTransformerEmbeddingProvider
from app.services.rag.types import EmbeddingFailureCode, EmbeddingStatus


class FakeEmbeddingModel:
    def __init__(self, vector):
        self.vector = vector
        self.calls = []

    def encode(self, sentences, *, normalize_embeddings):
        self.calls.append((sentences, normalize_embeddings))
        return [self.vector]


def test_disabled_embeddings_do_not_load_a_model():
    def unexpected_loader(_):
        raise AssertionError("disabled embeddings must not load a model")

    provider = LocalSentenceTransformerEmbeddingProvider(
        enabled=False,
        model_loader=unexpected_loader,
    )

    result = provider.embed("binary search")

    assert result.status is EmbeddingStatus.DISABLED
    assert result.failure_code is EmbeddingFailureCode.DISABLED
    assert result.vector is None


@pytest.mark.parametrize("text", ["", " \t\n "])
def test_empty_or_whitespace_input_is_typed_and_does_not_load_a_model(text):
    def unexpected_loader(_):
        raise AssertionError("empty input must not load a model")

    provider = LocalSentenceTransformerEmbeddingProvider(
        enabled=True,
        model_loader=unexpected_loader,
    )

    result = provider.embed(text)

    assert result.status is EmbeddingStatus.UNAVAILABLE
    assert result.failure_code is EmbeddingFailureCode.EMPTY_INPUT
    assert result.vector is None


def test_non_string_input_is_typed_and_does_not_load_a_model():
    def unexpected_loader(_):
        raise AssertionError("invalid input must not load a model")

    provider = LocalSentenceTransformerEmbeddingProvider(
        enabled=True,
        model_loader=unexpected_loader,
    )

    result = provider.embed(None)

    assert result.status is EmbeddingStatus.UNAVAILABLE
    assert result.failure_code is EmbeddingFailureCode.INVALID_INPUT
    assert result.vector is None


def test_model_load_failure_is_typed_and_logged(caplog):
    def unavailable_loader(_):
        raise RuntimeError("model cache is unavailable")

    provider = LocalSentenceTransformerEmbeddingProvider(
        enabled=True,
        model_loader=unavailable_loader,
    )

    with caplog.at_level(logging.ERROR):
        result = provider.embed("deadlock prevention")

    assert result.status is EmbeddingStatus.UNAVAILABLE
    assert result.failure_code is EmbeddingFailureCode.MODEL_LOAD_FAILED
    assert "model load failed" in caplog.text


def test_embedding_inference_failure_is_typed_and_logged(caplog):
    class FailingModel:
        def encode(self, sentences, *, normalize_embeddings):
            raise RuntimeError("inference failed")

    provider = LocalSentenceTransformerEmbeddingProvider(
        enabled=True,
        model_loader=lambda _: FailingModel(),
    )

    with caplog.at_level(logging.ERROR):
        result = provider.embed("normalization")

    assert result.status is EmbeddingStatus.UNAVAILABLE
    assert result.failure_code is EmbeddingFailureCode.EMBEDDING_FAILED
    assert "embedding failed" in caplog.text


def test_invalid_vector_is_typed_and_fail_open():
    provider = LocalSentenceTransformerEmbeddingProvider(
        enabled=True,
        model_loader=lambda _: FakeEmbeddingModel([0.1] * 383),
    )

    result = provider.embed("database indexing")

    assert result.status is EmbeddingStatus.UNAVAILABLE
    assert result.failure_code is EmbeddingFailureCode.INVALID_VECTOR
    assert result.vector is None


def test_valid_embedding_is_normalized_and_cached():
    model = FakeEmbeddingModel([0.1] * 384)
    loads = []

    def loader(model_name):
        loads.append(model_name)
        return model

    provider = LocalSentenceTransformerEmbeddingProvider(
        enabled=True,
        model_loader=loader,
    )

    first = provider.embed("primary key")
    second = provider.embed("foreign key")

    assert first.status is EmbeddingStatus.AVAILABLE
    assert first.vector == tuple([0.1] * 384)
    assert second.status is EmbeddingStatus.AVAILABLE
    assert loads == ["sentence-transformers/all-MiniLM-L6-v2"]
    assert model.calls == [
        (["primary key"], True),
        (["foreign key"], True),
    ]
