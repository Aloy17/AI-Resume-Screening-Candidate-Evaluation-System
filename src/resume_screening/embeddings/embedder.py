
"""
Semantic Embedding Engine

Uses Sentence Transformers to convert text into
numerical embeddings and calculate semantic similarity.
"""

import numpy as np
import torch

from sentence_transformers import SentenceTransformer
from functools import lru_cache


# ==================================================
# 1. MODEL CONFIGURATION
# ==================================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

EMBEDDING_DIMENSION = 384


# ==================================================
# 2. DEVICE CONFIGURATION
# ==================================================

def get_device():
    """
    Select the best available device.

    Apple Silicon Mac:
        Uses MPS when supported.

    Otherwise:
        Uses CPU.
    """

    if torch.backends.mps.is_available():
        return "mps"

    if torch.cuda.is_available():
        return "cuda"

    return "cpu"


# ==================================================
# 3. LOAD SENTENCE TRANSFORMER MODEL
# ==================================================

@lru_cache(maxsize=1)
def load_embedding_model():
    """
    Load the pretrained Sentence Transformer model.

    lru_cache ensures the model is loaded only once
    during the current Python process.
    """

    device = get_device()

    print(f"Loading embedding model: {MODEL_NAME}")
    print(f"Using device: {device}")

    model = SentenceTransformer(
        MODEL_NAME,
        device=device
    )

    print("Embedding model loaded successfully.")

    return model


# ==================================================
# 4. VALIDATE INPUT TEXT
# ==================================================

def validate_text(text):
    """
    Validate text before generating embeddings.
    """

    if not isinstance(text, str):
        raise TypeError("Input must be a string.")

    text = text.strip()

    if not text:
        raise ValueError("Input text cannot be empty.")

    return text


# ==================================================
# 5. GENERATE SINGLE TEXT EMBEDDING
# ==================================================

def generate_embedding(text):
    """
    Convert one text input into a numerical embedding.

    Returns:
        numpy.ndarray of shape (384,)
    """

    text = validate_text(text)

    model = load_embedding_model()

    embedding = model.encode(
        text,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    embedding = np.asarray(
        embedding,
        dtype=np.float32
    )

    if embedding.shape != (EMBEDDING_DIMENSION,):
        raise ValueError(
            f"Unexpected embedding shape: {embedding.shape}"
        )

    return embedding


# ==================================================
# 6. GENERATE MULTIPLE TEXT EMBEDDINGS
# ==================================================

def generate_embeddings(text_list):
    """
    Convert multiple text inputs into embeddings.

    Returns:
        numpy.ndarray of shape (number_of_texts, 384)
    """

    if not isinstance(text_list, list):
        raise TypeError("Input must be a list of strings.")

    if not text_list:
        raise ValueError("Text list cannot be empty.")

    validated_texts = [
        validate_text(text)
        for text in text_list
    ]

    model = load_embedding_model()

    embeddings = model.encode(
        validated_texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=32
    )

    embeddings = np.asarray(
        embeddings,
        dtype=np.float32
    )

    return embeddings


# ==================================================
# 7. CALCULATE COSINE SIMILARITY
# ==================================================

def calculate_cosine_similarity(
    embedding_a,
    embedding_b
):
    """
    Calculate cosine similarity between two embeddings.

    Since embeddings are normalized, their dot product
    gives the cosine similarity.
    """

    embedding_a = np.asarray(
        embedding_a,
        dtype=np.float32
    )

    embedding_b = np.asarray(
        embedding_b,
        dtype=np.float32
    )

    if embedding_a.shape != embedding_b.shape:
        raise ValueError(
            "Both embeddings must have the same dimensions."
        )

    if embedding_a.ndim != 1:
        raise ValueError(
            "Each embedding must be a one-dimensional vector."
        )

    norm_a = np.linalg.norm(embedding_a)
    norm_b = np.linalg.norm(embedding_b)

    if norm_a == 0 or norm_b == 0:
        raise ValueError(
            "Cannot calculate similarity for a zero vector."
        )

    similarity = np.dot(
        embedding_a,
        embedding_b
    ) / (norm_a * norm_b)

    return float(
        np.clip(similarity, -1.0, 1.0)
    )


# ==================================================
# 8. COMPARE TWO TEXTS
# ==================================================

def compare_texts(text_a, text_b):
    """
    Generate embeddings for two texts and
    calculate their semantic similarity.

    Returns:
        Dictionary containing both embeddings'
        similarity score.
    """

    embedding_a = generate_embedding(text_a)

    embedding_b = generate_embedding(text_b)

    similarity = calculate_cosine_similarity(
        embedding_a,
        embedding_b
    )

    return {
        "text_a": text_a,
        "text_b": text_b,
        "similarity_score": round(similarity, 4),
        "similarity_percentage": round(
            similarity * 100, 2
        )
    }


# ==================================================
# 9. COMPARE ONE TEXT AGAINST MULTIPLE TEXTS
# ==================================================

def compare_text_against_many(
    reference_text,
    comparison_texts
):
    """
    Compare one reference text against multiple texts.

    Useful for comparing a job responsibility against
    multiple candidate experience descriptions.
    """

    reference_text = validate_text(reference_text)

    if not isinstance(comparison_texts, list):
        raise TypeError(
            "comparison_texts must be a list."
        )

    if not comparison_texts:
        raise ValueError(
            "Comparison texts cannot be empty."
        )

    validated_texts = [
        validate_text(text)
        for text in comparison_texts
    ]

    reference_embedding = generate_embedding(
        reference_text
    )

    comparison_embeddings = generate_embeddings(
        validated_texts
    )

    similarities = np.dot(
        comparison_embeddings,
        reference_embedding
    )

    results = []

    for text, similarity in zip(
        validated_texts,
        similarities
    ):

        results.append({
            "text": text,
            "similarity_score": round(
                float(similarity), 4
            ),
            "similarity_percentage": round(
                float(similarity) * 100, 2
            )
        })

    results.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    return results
