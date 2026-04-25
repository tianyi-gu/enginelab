import { createFileRoute } from "@tanstack/react-router";
import ChessLab from "@/components/chess/ChessLab";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "ChessLab — Train & Play Custom Chess Engines" },
      {
        name: "description",
        content:
          "Pick evaluation features, watch agents battle in a training montage, then play the winning engine.",
      },
      { property: "og:title", content: "ChessLab — Train & Play Custom Chess Engines" },
      {
        property: "og:description",
        content:
          "Build a chess engine from evaluation features, simulate a tournament, then play the champion.",
      },
    ],
  }),
  component: Index,
});

function Index() {
  return <ChessLab />;
}
