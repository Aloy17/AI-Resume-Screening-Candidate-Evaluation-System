
import json

import numpy as np
import pytest

from resume_screening.embeddings import Embedder


class FakeModel:
    """Small stand-in for SentenceTransformer during tests."""

    def __init__(self):
        self.encode_calls = 0
        self.encoded_texts = []

    def encode(
        self,
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ):
        self.encode_calls += 1
        self.encoded_texts.extend(texts)

        vectors = []

        for text in texts:
            value = len(text)
            vectors.append([value, value + 1, value + 2])

        vectors = np.asarray(vectors, dtype=np.float32)

        if normalize_embeddings:
            vectors /= np.linalg.norm(
                vectors,
                axis=1,
                keepdims=True,
            )

        return vectors


def test_new_embeddings_are_saved_to_cache(tmp_path):
    cache_path = tmp_path / "embedding_cache.json"
    embedder = Embedder(cache_path=cache_path)
    model = FakeModel()
    embedder._load_model = lambda: model

    result = embedder.embed(["Python developer"])

    assert result.shape == (1, 3)
    assert cache_path.exists()

    cache = json.loads(cache_path.read_text(encoding="utf-8"))

    assert cache["model_name"] == embedder.model_name
    assert len(cache["embeddings"]) == 1
    assert model.encode_calls == 1


def test_existing_embeddings_are_reused(tmp_path):
    cache_path = tmp_path / "embedding_cache.json"

    first_embedder = Embedder(cache_path=cache_path)
    first_model = FakeModel()
    first_embedder._load_model = lambda: first_model

    original = first_embedder.embed(["Python developer"])

    second_embedder = Embedder(cache_path=cache_path)

    def unexpected_model_load():
        raise AssertionError("Model should not load for cached text.")

    second_embedder._load_model = unexpected_model_load

    reused = second_embedder.embed(["Python developer"])

    assert np.allclose(original, reused)


def test_only_missing_texts_are_encoded(tmp_path):
    cache_path = tmp_path / "embedding_cache.json"
    embedder = Embedder(cache_path=cache_path)
    model = FakeModel()
    embedder._load_model = lambda: model

    embedder.embed(["Python developer"])

    result = embedder.embed([
        "Python developer",
        "Java developer",
        "Java developer",
    ])

    assert result.shape == (3, 3)
    assert model.encode_calls == 2
    assert model.encoded_texts == [
        "Python developer",
        "Java developer",
    ]


def test_different_model_does_not_reuse_old_cache(tmp_path):
    cache_path = tmp_path / "embedding_cache.json"

    first = Embedder(
        model_name="model-one",
        cache_path=cache_path,
    )
    first_model = FakeModel()
    first._load_model = lambda: first_model
    first.embed(["Python developer"])

    second = Embedder(
        model_name="model-two",
        cache_path=cache_path,
    )
    second_model = FakeModel()
    second._load_model = lambda: second_model
    second.embed(["Python developer"])

    assert second_model.encode_calls == 1


def test_corrupted_cache_raises_clear_error(tmp_path):
    cache_path = tmp_path / "embedding_cache.json"
    cache_path.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Could not read embedding cache"):
        Embedder(cache_path=cache_path)
