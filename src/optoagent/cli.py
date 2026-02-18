"""
OptoAgent CLI — command-line interface for all agent operations.

Usage:
    optoagent <command> [options]

Commands:
    active_search    Search for papers
    run_cycle        Search + Summarize + Generate Ideas
    monitor_sources  Check tracked journals & groups
    list_papers      List stored papers
    list_ideas       List generated ideas
    add_experiment   Add an experiment record
    index_knowledge  Index local knowledge base for RAG
"""

import argparse

from optoagent.config import DEFAULT_LIMIT, DEFAULT_QUERY, EXA_API_KEY
from optoagent.logger import get_logger
from optoagent.models import Experiment
from optoagent.modules.idea_generator import IdeaGenerator
from optoagent.modules.notifier import FeishuNotifier
from optoagent.modules.searcher import PaperSearcher
from optoagent.modules.storage import Storage
from optoagent.modules.summarizer import PaperSummarizer
from optoagent.modules.vector_store import VectorStore

logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="OptoAgent CLI")
    parser.add_argument(
        "command",
        choices=[
            "add_experiment",
            "run_cycle",
            "list_papers",
            "list_ideas",
            "active_search",
            "monitor_sources",
            "index_knowledge",
        ],
        help="Command to execute",
    )
    parser.add_argument("--query", help="Search query for active search or run_cycle")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Number of papers to find")
    parser.add_argument("--title", help="Title for 'add_experiment'")
    parser.add_argument("--desc", help="Description for 'add_experiment'")
    parser.add_argument("--results", help="Results for 'add_experiment'")
    parser.add_argument("--chat_id", help="Feishu Chat ID for notifications")

    args = parser.parse_args()

    # Initialize services
    storage = Storage()
    vector_store = VectorStore()
    notifier = FeishuNotifier()
    searcher = PaperSearcher(exa_api_key=EXA_API_KEY)
    summarizer = PaperSummarizer()

    # ---- Command dispatch ----

    if args.command == "add_experiment":
        if not args.title or not args.desc:
            logger.error("--title and --desc are required for add_experiment")
            return
        exp = Experiment(
            title=args.title,
            description=args.desc,
            results=args.results or "Pending",
            status="ongoing",
        )
        storage.add_experiment(exp)
        logger.info("Experiment added successfully.")

    elif args.command == "list_papers":
        for p in storage.get_papers():
            print(f"- {p.title} ({p.url})")

    elif args.command == "list_ideas":
        for i in storage.get_ideas():
            print(f"- {i.title}\n  Reasoning: {i.reasoning[:100]}...")

    elif args.command == "index_knowledge":
        logger.info("Indexing knowledge base from 'data/knowledge'...")
        vector_store.index_documents()

    elif args.command in ("run_cycle", "active_search", "monitor_sources"):
        papers = []

        if args.command == "monitor_sources":
            logger.info("Monitoring tracked sources (Journals & Groups)...")
            papers = searcher.monitor_sources()
            if not papers:
                logger.info("No new papers found from tracked sources.")

        elif args.command in ("active_search", "run_cycle"):
            query = args.query or DEFAULT_QUERY
            papers = searcher.search_active(query, limit=args.limit)

        # Process papers: Summarize → Store → Notify
        new_papers = []
        for p in papers:
            existing = [ep for ep in storage.get_papers() if ep.title == p.title]
            if not existing:
                logger.info("Summarizing new paper: %s", p.title)
                p.summary = summarizer.summarize(p)
                storage.add_paper(p)
                new_papers.append(p)
                notifier.notify_new_paper(p, receive_id=args.chat_id)
            else:
                logger.info("Paper already exists: %s", p.title)

        if not new_papers:
            logger.info("No new papers found during this cycle.")

        # Generate ideas for run_cycle or monitor_sources with new papers
        if args.command == "run_cycle" or (args.command == "monitor_sources" and new_papers):
            all_papers = storage.get_papers()
            experiments = storage.get_experiments()

            if new_papers or all_papers:
                # RAG: retrieve relevant context
                context = ""
                if new_papers:
                    query_text = f"{new_papers[0].title} {new_papers[0].summary}"
                    logger.info("Retrieving context for: %s...", new_papers[0].title)
                    context = vector_store.query_similar_context(query_text)

                generator = IdeaGenerator()
                recent_papers = new_papers if new_papers else all_papers[-5:]
                idea = generator.generate_idea(recent_papers, experiments, context)

                storage.add_idea(idea)
                notifier.notify_new_idea(idea, receive_id=args.chat_id)
                logger.info("Generated new idea: %s", idea.title)
            else:
                logger.info("Not enough papers to generate ideas.")


if __name__ == "__main__":
    main()
