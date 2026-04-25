"""Result I/O for EngineLab — JSON and CSV persistence."""

import json
from pathlib import Path

from simulation.game import GameResult


def save_results_json(results: list[GameResult], path: str) -> None:
    """Save results to JSON file."""
    data = []
    for r in results:
        entry = {
            "white_agent": r.white_agent,
            "black_agent": r.black_agent,
            "winner": r.winner,
            "moves": r.moves,
            "termination_reason": r.termination_reason,
            "white_avg_nodes": r.white_avg_nodes,
            "black_avg_nodes": r.black_avg_nodes,
            "white_avg_time": r.white_avg_time,
            "black_avg_time": r.black_avg_time,
        }
        if r.move_list:
            entry["move_list"] = r.move_list
        data.append(entry)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_results_json(path: str) -> list[GameResult]:
    """Load results from JSON file."""
    with open(path) as f:
        data = json.load(f)
    return [
        GameResult(
            white_agent=d["white_agent"],
            black_agent=d["black_agent"],
            winner=d["winner"],
            moves=d["moves"],
            termination_reason=d["termination_reason"],
            white_avg_nodes=d["white_avg_nodes"],
            black_avg_nodes=d["black_avg_nodes"],
            white_avg_time=d["white_avg_time"],
            black_avg_time=d["black_avg_time"],
            move_list=d.get("move_list", []),
        )
        for d in data
    ]


def save_results_csv(results: list[GameResult], path: str) -> None:
    """Save results to CSV file."""
    import csv

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "white_agent", "black_agent", "winner", "moves",
        "termination_reason", "white_avg_nodes", "black_avg_nodes",
        "white_avg_time", "black_avg_time",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "white_agent": r.white_agent,
                "black_agent": r.black_agent,
                "winner": r.winner if r.winner is not None else "",
                "moves": r.moves,
                "termination_reason": r.termination_reason,
                "white_avg_nodes": r.white_avg_nodes,
                "black_avg_nodes": r.black_avg_nodes,
                "white_avg_time": r.white_avg_time,
                "black_avg_time": r.black_avg_time,
            })
