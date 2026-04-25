import { createFileRoute } from "@tanstack/react-router";
import ChessLab from "@/components/chess/ChessLab";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "EngineLab — Feature-Subset Engine Discovery" },
      {
        name: "description",
        content:
          "Select evaluation features, run a round-robin tournament, analyze which features drive wins, then play the champion engine.",
      },
      { property: "og:title", content: "EngineLab — Feature-Subset Engine Discovery" },
    ],
  }),
  component: Index,
});

function Index() {
  return <ChessLab />;
}
