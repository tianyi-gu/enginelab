"""CLI entry point for EngineLab.

Commands:
  random-game   Play random vs random
  match         Play specific feature sets against each other
  tournament    Run round-robin tournament
  analyze       Analyze existing results JSON
  full-pipeline End-to-end pipeline
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="EngineLab — Feature-subset strategy discovery for chess variants")
console = Console()


@app.command()
def random_game(
    variant: str = typer.Option("standard", help="Chess variant"),
    max_moves: int = typer.Option(80, help="Max plies per game"),
    seed: int = typer.Option(42, help="Random seed"),
) -> None:
    """Play a random-vs-random game."""
    from simulation.random_agent import RandomAgent
    from simulation.game import play_game

    white = RandomAgent(seed=seed)
    black = RandomAgent(seed=seed + 1)
    result = play_game(white, black, variant=variant, max_moves=max_moves, seed=seed)

    console.print(f"[bold]Random vs Random[/bold] ({variant})")
    console.print(f"Winner: {result.winner or 'draw'}")
    console.print(f"Moves: {result.moves}")
    console.print(f"Reason: {result.termination_reason}")


@app.command()
def match(
    white: str = typer.Option(..., help="Comma-separated features for white"),
    black: str = typer.Option(..., help="Comma-separated features for black"),
    variant: str = typer.Option("standard", help="Chess variant"),
    depth: int = typer.Option(2, help="Search depth"),
    max_moves: int = typer.Option(80, help="Max plies per game"),
    seed: int = typer.Option(42, help="Random seed"),
) -> None:
    """Play a match between two feature-set agents."""
    from agents.feature_subset_agent import FeatureSubsetAgent
    from simulation.game import play_game

    white_feats = tuple(sorted(f.strip() for f in white.split(",")))
    black_feats = tuple(sorted(f.strip() for f in black.split(",")))

    white_agent = FeatureSubsetAgent(
        name="Agent_" + "__".join(white_feats),
        features=white_feats,
        weights={f: 1.0 / len(white_feats) for f in white_feats},
    )
    black_agent = FeatureSubsetAgent(
        name="Agent_" + "__".join(black_feats),
        features=black_feats,
        weights={f: 1.0 / len(black_feats) for f in black_feats},
    )

    result = play_game(
        white_agent, black_agent,
        variant=variant, depth=depth, max_moves=max_moves, seed=seed,
    )

    console.print(f"[bold]{white_agent.name} vs {black_agent.name}[/bold]")
    console.print(f"Winner: {result.winner or 'draw'}")
    console.print(f"Moves: {result.moves}")
    console.print(f"Reason: {result.termination_reason}")
    console.print(f"White avg nodes: {result.white_avg_nodes:.0f}")
    console.print(f"Black avg nodes: {result.black_avg_nodes:.0f}")


@app.command()
def tournament(
    variant: str = typer.Option("standard", help="Chess variant"),
    depth: int = typer.Option(2, help="Search depth"),
    max_moves: int = typer.Option(80, help="Max plies per game"),
    seed: int = typer.Option(42, help="Random seed"),
    max_agents: int = typer.Option(100, help="Max number of agents"),
    output: str = typer.Option(None, help="Output JSON path"),
) -> None:
    """Run a round-robin tournament."""
    from agents.feature_subset_agent import FeatureSubsetAgent
    from tournament.round_robin import run_round_robin
    from tournament.leaderboard import compute_leaderboard
    from tournament.results_io import save_results_json

    agents = _get_agents(max_agents=max_agents, seed=seed)
    console.print(f"[bold]Tournament[/bold]: {len(agents)} agents, {variant}")
    console.print(f"Games: {len(agents) * (len(agents) - 1)}")

    results = run_round_robin(agents, variant, depth, max_moves, seed)

    lb = compute_leaderboard(results, agents)
    _print_leaderboard(lb)

    if output is None:
        output = f"outputs/data/tournament_results_{variant}.json"
    save_results_json(results, output)
    console.print(f"\nResults saved to {output}")


@app.command()
def analyze(
    input: str = typer.Option(..., help="Input results JSON path"),
    top_k: int = typer.Option(10, help="Top-K for marginal analysis"),
) -> None:
    """Analyze existing tournament results."""
    from agents.feature_subset_agent import FeatureSubsetAgent
    from tournament.results_io import load_results_json
    from tournament.leaderboard import compute_leaderboard
    from analysis.feature_marginals import compute_feature_marginals
    from analysis.synergy import compute_pairwise_synergies
    from analysis.interpretation import generate_interpretation

    results = load_results_json(input)
    console.print(f"Loaded {len(results)} game results")

    agents = _agents_from_results(results)
    lb = compute_leaderboard(results, agents)
    _print_leaderboard(lb)

    feature_names = sorted({f for a in agents for f in a.features})
    marginals = compute_feature_marginals(lb, feature_names, top_k=top_k)
    synergies = compute_pairwise_synergies(lb, feature_names)

    _print_marginals(marginals)
    _print_synergies(synergies)

    if lb:
        interp = generate_interpretation(lb[0], marginals, synergies, "unknown")
        console.print(f"\n[bold]Interpretation:[/bold] {interp}")


@app.command()
def full_pipeline(
    variant: str = typer.Option("standard", help="Chess variant"),
    depth: int = typer.Option(2, help="Search depth"),
    max_moves: int = typer.Option(80, help="Max plies per game"),
    seed: int = typer.Option(42, help="Random seed"),
    max_agents: int = typer.Option(100, help="Max number of agents"),
    top_k: int = typer.Option(10, help="Top-K for marginal analysis"),
) -> None:
    """Run the full EngineLab pipeline end-to-end."""
    from agents.feature_subset_agent import FeatureSubsetAgent
    from tournament.round_robin import run_round_robin
    from tournament.leaderboard import compute_leaderboard
    from tournament.results_io import save_results_json
    from analysis.feature_marginals import compute_feature_marginals
    from analysis.synergy import compute_pairwise_synergies
    from analysis.interpretation import generate_interpretation
    from reports.markdown_report import generate_markdown_report

    console.print("[bold]EngineLab Full Pipeline[/bold]")
    console.print(f"Variant: {variant}")
    console.print(f"Depth: {depth}, Max moves: {max_moves}, Seed: {seed}")
    console.print()

    # Step 1: Generate agents
    agents = _get_agents(max_agents=max_agents, seed=seed)
    feature_names = sorted({f for a in agents for f in a.features})
    console.print(f"Features: {', '.join(feature_names)}")
    console.print(f"Agents: {len(agents)}")
    n_games = len(agents) * (len(agents) - 1)
    console.print(f"Games to play: {n_games}")
    console.print()

    # Step 2: Run tournament
    results = run_round_robin(agents, variant, depth, max_moves, seed)

    # Step 3: Compute leaderboard
    lb = compute_leaderboard(results, agents)
    _print_leaderboard(lb, top_k)

    # Step 4: Feature marginals
    marginals = compute_feature_marginals(lb, feature_names, top_k=top_k)
    _print_marginals(marginals)

    # Step 5: Pairwise synergies
    synergies = compute_pairwise_synergies(lb, feature_names)
    _print_synergies(synergies)

    # Step 6: Interpretation
    if lb:
        interp = generate_interpretation(lb[0], marginals, synergies, variant)
        console.print(f"\n[bold]Interpretation:[/bold]\n{interp}")
    else:
        interp = "No results to interpret."

    # Step 7: Save results
    data_path = f"outputs/data/tournament_results_{variant}.json"
    save_results_json(results, data_path)
    console.print(f"\nResults saved to {data_path}")

    # Step 8: Generate report
    report_path = f"outputs/reports/{variant}_strategy_report.md"
    config = {
        "variant": variant, "depth": depth, "max_moves": max_moves,
        "seed": seed, "agents": len(agents), "games": n_games,
    }
    generate_markdown_report(
        variant=variant, feature_names=feature_names, leaderboard=lb,
        marginals=marginals, synergies=synergies, interpretation=interp,
        output_path=report_path, config=config,
    )
    console.print(f"Report saved to {report_path}")


def _get_agents(max_agents: int = 100, seed: int = 42):
    """Get agents — try real generation, fall back to material-only."""
    from agents.feature_subset_agent import FeatureSubsetAgent
    try:
        from agents.generate_agents import generate_feature_subset_agents
        from features.registry import get_feature_names
        feature_names = get_feature_names()
        if feature_names:
            return generate_feature_subset_agents(
                feature_names, max_agents=max_agents, seed=seed,
            )
    except (NotImplementedError, ImportError):
        pass

    # Fallback: material-only agent for Foundation
    return [
        FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0}),
    ]


def _agents_from_results(results) -> list:
    """Reconstruct minimal agents from result agent names."""
    from agents.feature_subset_agent import FeatureSubsetAgent
    names = set()
    for r in results:
        names.add(r.white_agent)
        names.add(r.black_agent)

    agents = []
    for name in sorted(names):
        if name.startswith("Agent_"):
            feat_str = name[len("Agent_"):]
            feats = tuple(sorted(feat_str.split("__")))
            weights = {f: 1.0 / len(feats) for f in feats}
            agents.append(FeatureSubsetAgent(name, feats, weights))
        else:
            agents.append(FeatureSubsetAgent(name, (), {}))
    return agents


def _print_leaderboard(lb, limit: int = 10) -> None:
    """Print top-N leaderboard as a rich table."""
    table = Table(title="Leaderboard")
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Agent", style="bold")
    table.add_column("Features")
    table.add_column("Rate", justify="right", style="green")
    table.add_column("W", justify="right")
    table.add_column("L", justify="right")
    table.add_column("D", justify="right")
    table.add_column("Games", justify="right")

    for i, row in enumerate(lb[:limit], 1):
        feats = ", ".join(row.features)
        table.add_row(
            str(i), row.agent_name, feats,
            f"{row.score_rate:.3f}",
            str(row.wins), str(row.losses), str(row.draws),
            str(row.games_played),
        )
    console.print(table)


def _print_marginals(marginals) -> None:
    """Print feature marginals as a rich table."""
    table = Table(title="Feature Contributions")
    table.add_column("Feature", style="bold")
    table.add_column("Avg With", justify="right")
    table.add_column("Avg Without", justify="right")
    table.add_column("Marginal", justify="right", style="green")
    table.add_column("Top-K Freq", justify="right")

    for m in marginals:
        table.add_row(
            m.feature,
            f"{m.avg_score_with:.3f}",
            f"{m.avg_score_without:.3f}",
            f"{m.marginal:+.3f}",
            f"{m.top_k_frequency:.2f}",
        )
    console.print(table)


def _print_synergies(synergies, limit: int = 10) -> None:
    """Print top synergies as a rich table."""
    table = Table(title="Top Synergies")
    table.add_column("Feature A", style="bold")
    table.add_column("Feature B", style="bold")
    table.add_column("Avg Both", justify="right")
    table.add_column("Synergy", justify="right", style="green")

    for s in synergies[:limit]:
        table.add_row(
            s.feature_a, s.feature_b,
            f"{s.avg_score_with_both:.3f}",
            f"{s.synergy:+.3f}",
        )
    console.print(table)


@app.command()
def play(
    variant: str = typer.Option("atomic", help="Chess variant"),
    depth: int = typer.Option(3, help="Engine search depth"),
    features: str = typer.Option(None, help="Comma-separated features (default: best known)"),
    color: str = typer.Option("w", help="Your color: w or b"),
) -> None:
    """Play interactively against the best engine agent."""
    from core.board import Board
    from core.move import Move
    from core.coordinates import algebraic_to_square, square_to_algebraic
    from agents.feature_subset_agent import FeatureSubsetAgent
    from search.alpha_beta import AlphaBetaEngine
    from variants.base import get_apply_move, get_generate_legal_moves

    # Build agent
    if features:
        feat_tuple = tuple(sorted(f.strip() for f in features.split(",")))
    else:
        # Best known from atomic tournaments
        feat_tuple = ("capture_threats", "king_safety", "mobility")

    weights = {f: 1.0 / len(feat_tuple) for f in feat_tuple}
    agent_name = "Agent_" + "__".join(feat_tuple)
    agent = FeatureSubsetAgent(agent_name, feat_tuple, weights)
    engine = AlphaBetaEngine(agent, depth, variant=variant)

    apply_fn = get_apply_move(variant)
    gen_legal_fn = get_generate_legal_moves(variant)

    board = Board.starting_position()
    console.print(f"\n[bold]EngineLab Interactive Play[/bold]")
    console.print(f"Variant: {variant} | Engine: {agent_name} (depth {depth})")
    console.print(f"You are [bold]{'White' if color == 'w' else 'Black'}[/bold]")
    console.print(f"Enter moves as UCI (e.g. e2e4, a7a8q for promotion)")
    console.print(f"Type [bold]quit[/bold] to exit, [bold]moves[/bold] to see legal moves\n")

    engine_color = "b" if color == "w" else "w"

    while not board.is_terminal():
        _render_board(board, console)

        legal = gen_legal_fn(board)
        if not legal:
            if board.side_to_move == color:
                console.print("[red]No legal moves — you lose![/red]")
            else:
                console.print("[green]Engine has no legal moves — you win![/green]")
            break

        if board.side_to_move == engine_color:
            console.print("[dim]Engine thinking...[/dim]", end="")
            move = engine.choose_move(board)
            uci = move.to_uci()
            console.print(
                f"\r[bold cyan]Engine plays:[/bold cyan] {uci}"
                f"  [dim]({engine.nodes_searched} nodes, "
                f"{engine.search_time_seconds:.2f}s)[/dim]"
            )
            board = apply_fn(board, move)
        else:
            while True:
                try:
                    raw = console.input("[bold green]Your move> [/bold green]").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    console.print("\nGoodbye!")
                    return

                if raw == "quit":
                    console.print("Goodbye!")
                    return
                if raw == "moves":
                    move_strs = sorted(m.to_uci() for m in legal)
                    console.print(f"Legal: {', '.join(move_strs)}")
                    continue

                # Parse UCI
                if len(raw) < 4:
                    console.print("[red]Invalid. Use UCI format like e2e4[/red]")
                    continue
                try:
                    start = algebraic_to_square(raw[0:2])
                    end = algebraic_to_square(raw[2:4])
                    promo = raw[4].upper() if len(raw) > 4 else None
                    if color == "b" and promo:
                        promo = promo.lower()
                    candidate = Move(start=start, end=end, promotion=promo)
                except (ValueError, IndexError):
                    console.print("[red]Invalid. Use UCI format like e2e4[/red]")
                    continue

                if candidate in legal:
                    board = apply_fn(board, candidate)
                    break
                else:
                    console.print("[red]Illegal move. Type 'moves' to see options.[/red]")

    if board.is_terminal():
        _render_board(board, console)
        if board.winner == color:
            console.print("[bold green]You win![/bold green]")
        elif board.winner == engine_color:
            console.print("[bold red]Engine wins![/bold red]")
        elif board.winner == "draw":
            console.print("[bold yellow]Draw![/bold yellow]")
        else:
            console.print(f"[bold]Game over. Winner: {board.winner}[/bold]")


def _render_board(board, console) -> None:
    """Render the board with Unicode pieces."""
    piece_unicode = {
        "K": "\u2654", "Q": "\u2655", "R": "\u2656", "B": "\u2657", "N": "\u2658", "P": "\u2659",
        "k": "\u265a", "q": "\u265b", "r": "\u265c", "b": "\u265d", "n": "\u265e", "p": "\u265f",
    }
    console.print()
    for rank in range(7, -1, -1):
        row = f"  {rank + 1} "
        for col in range(8):
            p = board.grid[rank][col]
            sq_dark = (rank + col) % 2 == 0
            bg = "on grey23" if sq_dark else "on grey50"
            ch = piece_unicode.get(p, " ")
            row += f"[{bg}] {ch} [/{bg}]"
        console.print(row)
    console.print("     a  b  c  d  e  f  g  h")
    console.print(f"  [dim]{board.side_to_move} to move | ply {board.move_count}[/dim]\n")


if __name__ == "__main__":
    app()
