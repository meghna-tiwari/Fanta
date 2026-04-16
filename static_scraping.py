from tavily import TavilyClient
import json
import time

client = TavilyClient(api_key="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")

def run_deep_scraper(categories, locations):
    master_dataset = []
    
    for cat in categories:
        for loc in locations:
            query = f"List of {cat} conferences and tech events in {loc} 2025 2026"
            print(f"🔍 Deep Scraping: {query}")
            
            try:
                # 1. Search for a list of URLs
                search = client.search(query=query, search_depth="advanced", max_results=10)
                urls = [r["url"] for r in search["results"]]
                
                # 2. Extract full content from all URLs in one batch
                # Tavily /extract is optimized for LLM-ready markdown/text
                extraction = client.extract(urls=urls)
                
                for i, res in enumerate(extraction["results"]):
                    master_dataset.append({
                        "event_id": f"{cat}_{loc}_{i}",
                        "category": cat,
                        "location": loc,
                        "url": res["url"],
                        "raw_content": res["raw_content"], # This is the "Gold" for your agents
                        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
            except Exception as e:
                print(f"⚠️ Error scraping {query}: {e}")
            
            time.sleep(1) # Respect rate limits

    # Save as the "Master Knowledge Base"
    with open("master_event_data.json", "w", encoding="utf-8") as f:
        json.dump(master_dataset, f, indent=4)
    print(f"✅ Master dataset built with {len(master_dataset)} deep-dive records.")

if __name__ == "__main__":
    # Expand these lists to get "Suitable Amount of Data"
    cats = ["AI", "SaaS", "Web3", "Mechanical Engineering", "Fintech"]
    locs = ["India", "USA", "Europe", "Singapore"]
    run_deep_scraper(cats, locs)