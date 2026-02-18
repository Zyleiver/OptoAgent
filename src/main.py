import argparse
import sys
import os
from dotenv import load_dotenv
from modules.knowledge_base import KnowledgeBase
from modules.searcher import PaperSearcher
from modules.summarizer import PaperSummarizer
from modules.idea_generator import IdeaGenerator
from modules.notifier import FeishuNotifier
from models import Experiment

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="OptoAgent CLI")
    parser.add_argument("command", choices=["add_experiment", "run_cycle", "list_papers", "list_ideas", "active_search", "monitor_sources", "index_knowledge"], help="Command to execute")
    parser.add_argument("--query", help="Search query for active search or run_cycle")
    parser.add_argument("--limit", type=int, default=5, help="Number of papers to find")
    # parser.add_argument("--rss", help="Comma-separated RSS Feed URLs") # Deprecated in favor of config
    parser.add_argument("--title", help="Title for 'add_experiment'")
    parser.add_argument("--desc", help="Description for 'add_experiment'")
    parser.add_argument("--results", help="Results for 'add_experiment'")
    
    args = parser.parse_args()
    
    # Initialize keys from Env
    exa_key = os.getenv("EXA_API_KEY")
    feishu_webhook = os.getenv("FEISHU_WEBHOOK")
    
    kb = KnowledgeBase()
    notifier = FeishuNotifier(webhook_url=feishu_webhook)
    searcher = PaperSearcher(exa_api_key=exa_key)
    summarizer = PaperSummarizer() # Auto-loads keys internally

    if args.command == "add_experiment":
        if not args.title or not args.desc:
            print("Error: --title and --desc are required for add_experiment")
            return
        exp = Experiment(title=args.title, description=args.desc, results=args.results or "Pending", status="ongoing")
        kb.add_experiment(exp)
        print("Experiment added successfully.")

    elif args.command == "list_papers":
        papers = kb.get_papers()
        for p in papers:
            print(f"- {p.title} ({p.url})")

    elif args.command == "list_ideas":
        ideas = kb.get_ideas()
        for i in ideas:
            print(f"- {i.title}\n  Reasoning: {i.reasoning[:100]}...")

    elif args.command == "index_knowledge":
        print("Indexing knowledge base from 'data/knowledge'...")
        kb.index_documents()
        
    elif args.command in ["run_cycle", "active_search", "monitor_sources"]:
        
        papers = []
        if args.command == "monitor_sources":
            print("Monitoring tracked sources (Journals & Groups)...")
            papers = searcher.monitor_sources()
            if not papers:
               print("No new papers found from tracked sources.")
        
        elif args.command == "active_search" or args.command == "run_cycle":
            query = args.query or "perovskite solar cells"
            # Use Exa if key exists, else simulate
            papers = searcher.search_active(query, limit=args.limit)

        # Process papers (Summarize -> Store -> Notify)
        new_papers = []
        for p in papers:
            # Check if already exists
            existing = [ep for ep in kb.get_papers() if ep.title == p.title]
            if not existing:
                print(f"Summarizing new paper: {p.title}")
                p.summary = summarizer.summarize(p)
                kb.add_paper(p)
                new_papers.append(p)
                notifier.notify_new_paper(p)
            else:
                print(f"Paper already exists: {p.title}")

        if not new_papers:
            print("No new papers found during this cycle.")
        
        # for 'run_cycle', we also generate ideas
        if args.command == "run_cycle" or (args.command == "monitor_sources" and new_papers):
             # 3. Generate Ideas
            all_papers = kb.get_papers()
            experiments = kb.get_experiments()
            
            if new_papers or all_papers:
                # Use RAG to get relevant context
                context = ""
                if new_papers:
                     query_text = f"{new_papers[0].title} {new_papers[0].summary}"
                     print(f"Retrieving context for: {new_papers[0].title}...")
                     context = kb.query_similar_context(query_text)
                
                generator = IdeaGenerator()
                # Use recent papers + RAG context
                recent_papers = new_papers if new_papers else all_papers[-5:]
                idea = generator.generate_idea(recent_papers, experiments, context)
                
                kb.add_idea(idea)
                notifier.notify_new_idea(idea)
                print(f"Generated new idea: {idea.title}")
            else:
                print("Not enough papers to generate ideas.")

if __name__ == "__main__":
    main()
