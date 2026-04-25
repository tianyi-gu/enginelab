## Intro

We weren’t constrained to just standard Chess, though. After all, there are infinite ways to modify Chess. You can make captures trigger explosions that wipe out nearby pieces. You can flip the objective entirely so that the goal is to lose all your pieces instead of protecting them.

So we asked: is it possible, given any variant, to systematically and quickly develop an engine that can hold its own? We thought this was a more interesting question to answer, and perhaps we could also walk away with some practical lessons on how to collaborate with agentic AI. 

Well, EngineLab was our answer to that question. At a high level, it agentically modifies a deterministic algorithm to adapt an engine to different variants. 

## Research and planning

To better understand how AI could help our development process, we sifted through literature and media. Following the footsteps of professional researchers, we treated AI as a conversation partner that we can enrich but also challenge our ideas. From the ChatDev framework, we utilized an engineering harness with supervising agents, planning agents, and execution agents, and more. 

On the chess side, we found a deterministic algorithm known as Alpha-Beta pruning. We hypothesized that by varying the types of features we feed the evaluation function for a variant, we can create a tournament style to figure out which set of features lead to the best engine.

## AI Usage, Process/Parallelization, and Architecture

Suppose our universe set of features contains 10 features. Once we’ve picked our variation, it will not always be the case we want all of them to be considered. So the question is, which features should we feed our evaluation function? 

One naive approach is to assign an agent to every possible combination of features and modify the evaluation code accordingly. But this is not computationally feasible. Another naive approach would be to limit the number of subsets by randomly sampling which ones we will consider. However, this process is not rigorous, and the engine output will have high variance. 

We wanted a method that balances coverage and rigor. In the end, we chose to use an LLM to select what it thinks are the 7 most-likely features to be in the optimal engine of this type. Then, we instantiate 2^7 - 1 = 127 agents to exhaustively consider all possible combinations of features to cover. These agents face off in a round-robin tournament, and the agent with the most wins is our final engine. Our round robin tournament will have thousands of games, so we will also parallelize the process.

Finally, we implement interpretability by tracking statistics such as win rates, data visualizations, and which features were tracked in the highest-ranked engines. 

Having decided the structure of our project, we spent an hour writing files to plan our AI agent prompting. Instructions.md defined exactly what to build, AGENTS.md to establish strict behavioral guardrails for how the AI should plan and test its code, and interfaces.md predefined every single function signature the two modules would use to communicate. LLMs were used here to enrich our files, but we did have to intervene at times to correct for times the AI lost focus.

At 2 am, we began coding. We had parallelized the workstream with git worktrees: one developer had multiple agents creating the chess variants and Alpha-Beta search, while another built the parallel tournament and testing infrastructure. We also enforced adversarial AI code review, writing unit tests and Perft tests.

We were able to split the workstream up among our team, and we were able to get an MVP within 3 hours. 

## Closing thoughts

We are optimistic about the project. With more computers, our training would be able to consider further depth. Looking forward, we also think that this architecture could be generalizable to other zero-sum games. 
