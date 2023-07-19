import argparse
from typing import List

import numpy as np
from transformers import BertModel, BertTokenizer, AutoTokenizer
from scipy.special import softmax

from embeddings import e5_model_embeddings
from sg import parse_url, query_highlighted_file_line_range


def get_line_windows(lines: List[str], window_size: int):
    """
    Split the lines into overlapping windows of size window_size.
    """
    windows = []
    for i in range(-window_size + 1, len(lines)):
        start_line = max(0, i)
        end_line = min(len(lines), i + window_size)

        content = "\n".join(lines[start_line:end_line]).rstrip()
        if len(content) == 0:
            continue

        windows.append(
            {"content": content, "startLine": start_line, "endLine": end_line}
        )
    return windows


def page_rank(embeddings: np.ndarray, d=0.85, n_iterations=10) -> List[float]:
    """
    Applies the PageRank algorithm on an adjecency matrix constructed from embedding similarities.
    Returns a list of PageRank scores for each embedding.
    """
    adj_matrix = np.matmul(embeddings, embeddings.T)
    # Remove self-edges (embedding cannot point to itself).
    np.fill_diagonal(adj_matrix, 0.0)

    n_samples = adj_matrix.shape[0]
    # Convert the adjecency matrix to a column stochastic transition matrix.
    transition_matrix = softmax(adj_matrix, axis=0)
    # Apply the damping parameter.
    transition_matrix = d * transition_matrix + (1 - d) / n_samples

    # Run the PageRank power method. Not super optimal, but works reasonably fast for smaller matrices.
    scores = np.ones(n_samples, dtype=np.float32) / n_samples
    for _ in range(n_iterations):
        new_scores = transition_matrix @ scores

        if np.allclose(scores, new_scores):
            break

        scores = new_scores

    return scores.tolist()


def glance(
    model: BertModel,
    tokenizer: BertTokenizer,
    content: str,
    window_size: int,
    device="cpu",
):
    """
    Get a "glance" at the important lines in the content.
    """
    line_windows = get_line_windows(content.split("\n"), window_size)
    embeddings = e5_model_embeddings(
        model, tokenizer, [window["content"] for window in line_windows], device=device
    )
    scores = page_rank(embeddings)

    scored_windows = [
        {**window, "score": score} for score, window in zip(scores, line_windows)
    ]
    return sorted(scored_windows, key=lambda window: window["score"], reverse=True)


def main(args):
    model = BertModel.from_pretrained(args.model).to(args.device).eval()
    tokenizer = AutoTokenizer.from_pretrained(args.model)

    if args.file.startswith("https://sourcegraph.com"):
        repo_name, commit_id, file_path = parse_url(args.file)

        content, _ = query_highlighted_file_line_range(
            repo_name,
            commit_id,
            file_path,
            0,
            2**31 - 1,
        )
    else:
        with open(args.file, encoding="utf-8") as f:
            content = f.read()

    windows = glance(model, tokenizer, content, args.window_size, device=args.device)
    for window in windows[: args.top]:
        print(
            f"Content (lines {window['startLine']}-{window['endLine']}, score {window['score']:.5f}):"
        )
        print("```")
        print(window["content"])
        print("```")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", dest="model")
    parser.add_argument("--file", dest="file")
    parser.add_argument("--device", dest="device", default="cpu")
    parser.add_argument("--window-size", dest="window_size", type=int, default=5)
    parser.add_argument("--top", dest="top", type=int, default=5)
    args = parser.parse_args()

    main(args)
