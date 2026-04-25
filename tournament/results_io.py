"""Result I/O — JSON and CSV serialization for GameResult lists."""

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from simulation.game import GameResult


def save_results_json(results: list[GameResult], path: str | Path) -> None:
    """Serialize a list of GameResults to a JSON file.

    Args:
        results: Game results to persist.
        path:    Destination file path (str or Path).

    Raises:
        OSError: If the file cannot be written.
    """
    target = Path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(r) for r in results]
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Failed to write results JSON to {target}: {exc}") from exc


def load_results_json(path: str | Path) -> list[GameResult]:
    """Deserialize a list of GameResults from a JSON file.

    Args:
        path: Source file path (str or Path).

    Returns:
        List of GameResult objects.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError:        If the JSON is malformed or missing required fields.
        OSError:           If the file cannot be read.
    """
    source = Path(path)
    try:
        raw = source.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Results JSON not found: {source}")
    except OSError as exc:
        raise OSError(f"Failed to read results JSON from {source}: {exc}") from exc

    try:
        payload: list[dict] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON in {source}: {exc}") from exc

    results: list[GameResult] = []
    for i, item in enumerate(payload):
        try:
            results.append(
                GameResult(
                    white_agent=item["white_agent"],
                    black_agent=item["black_agent"],
                    winner=item["winner"],
                    moves=item["moves"],
                    termination_reason=item["termination_reason"],
                    white_avg_nodes=float(item["white_avg_nodes"]),
                    black_avg_nodes=float(item["black_avg_nodes"]),
                    white_avg_time=float(item["white_avg_time"]),
                    black_avg_time=float(item["black_avg_time"]),
                )
            )
        except (KeyError, TypeError) as exc:
            raise ValueError(
                f"Missing or invalid field in result at index {i}: {exc}"
            ) from exc

    return results


def save_results_csv(results: list[GameResult], path: str | Path) -> None:
    """Serialize a list of GameResults to a CSV file via pandas.

    Args:
        results: Game results to persist.
        path:    Destination file path (str or Path).

    Raises:
        OSError: If the file cannot be written.
    """
    target = Path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        rows = [asdict(r) for r in results]
        df = pd.DataFrame(rows)
        df.to_csv(target, index=False)
    except OSError as exc:
        raise OSError(f"Failed to write results CSV to {target}: {exc}") from exc
