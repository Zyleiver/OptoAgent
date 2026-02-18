import csv
import json
import os
import argparse

def import_csv(csv_path, json_path="tracking_sources.json"):
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found.")
        return

    # Load existing JSON
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"rss_feeds": [], "research_groups": []}
    else:
        data = {"rss_feeds": [], "research_groups": []}

    if "rss_feeds" not in data:
        data["rss_feeds"] = []

    # Read CSV
    added_count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        # Check header
        header = next(reader, None)
        # Heuristic: if first row looks like URL, treat as data. Else assume header.
        if header and not header[0].startswith("http"):
            pass # Skip header
        else:
            # First row was data
             if header:
                url = header[1] if len(header) > 1 else header[0]
                if url.startswith("http") and url not in data["rss_feeds"]:
                    data["rss_feeds"].append(url)
                    added_count += 1

        for row in reader:
            if not row: continue
            # Assume format: Name, URL OR just URL
            # If 2 columns, 2nd is URL. If 1, 1st is URL.
            url = row[1] if len(row) > 1 else row[0]
            url = url.strip()
            
            if url.startswith("http"):
                if url not in data["rss_feeds"]:
                    data["rss_feeds"].append(url)
                    added_count += 1
                    print(f"Added: {url}")
                else:
                    print(f"Skipped (duplicate): {url}")

    # Save
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"\nSuccessfully added {added_count} new RSS feeds to {json_path}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import RSS feeds from CSV")
    parser.add_argument("csv_file", help="Path to CSV file (Format: Name, URL)")
    args = parser.parse_args()
    
    import_csv(args.csv_file)
