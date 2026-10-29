# Jarvis

A simple attempt at building a personal research and study agent. Initial part at this moment just has a very basic rag pipeline with an ingester and a Weaviate db as a vector store.

## Things to add
~~ 1. Web search ~~
~~ 2. tools to open ai and try it~~
~~ 3. add extra tools ~~
~~ 4. agentic loop ~~
~~ 5. langgraph agent ~~
6. Monitoring and observability
7. Guardrails
8. Injection
9. Evals
10. Chunking Strategies
11. production architecture


the agent implemented atp is a very simple one and could be prone to mistakes.

In a proper agentic system (since this is a study agent)

- All our notes must be ingested along with whatever we upload to the agent
- any changes to notes will require that note to be ** re-indexed ** 
- we would also need to have context across questions (checkpointing and LTM and STM)
- Human in the loop etc for sensitive actions