from tavily import TavilyClient
import json
import time
import os

# --- KEYS ---
TAVILY_KEY = "tavily"
client = TavilyClient(api_key=TAVILY_KEY)

def load_static_benchmarks():
    """
    STATIC LAYER: Loads verified industry benchmarks from local storage.
    """
    try:
        if os.path.exists("static_library.json"):
            with open("static_library.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load static library: {e}")
    return []

def run_hybrid_deep_scraper(categories, locations):
    master_dataset = []
    
    # 1. LOAD STATIC DATA FIRST
    print("📂 Loading Static Knowledge Base...")
    static_benchmarks = load_static_benchmarks()
    
    # 2. START DYNAMIC LOOP
    for cat in categories:
        for loc in locations:
            query = f"Full list of {cat} conferences {loc} 2025 2026 speakers sponsors pricing"
            print(f"\n🔍 Deep Scraping: {query}")
            
            try:
                # REFINEMENT: Search depth advanced to find deep tables/lists
                search = client.search(query=query, search_depth="advanced", max_results=10)
                urls = [r["url"] for r in search["results"]]
                
                # REFINEMENT: Advanced Extraction to get tables and hidden text
                # We limit to top 5 URLs to maximize extraction quality per site
                extraction = client.extract(urls=urls[:5]) 
                
                for i, res in enumerate(extraction["results"]):
                    # Find matching static benchmark for context
                    match = next((b for b in static_benchmarks if cat.lower() in b['category'].lower()), {})
                    
                    master_dataset.append({
                        "event_id": f"{cat}_{loc}_{i}",
                        "category": cat,
                        "location": loc,
                        "url": res["url"],
                        "raw_content": res["raw_content"], # The 'Gold' data
                        "static_reference": match.get("benchmarks", {}), # Injects static data
                        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
            except Exception as e:
                print(f"⚠️ Error scraping {query}: {e}")
            
            time.sleep(1.5) # Slight delay to keep extraction quality high

    # 3. SAVE HYBRID DATASET
    with open("master_event_data2.json", "w", encoding="utf-8") as f:
        json.dump(master_dataset, f, indent=4)
    
    print(f"\n✅ Hybrid Master Dataset built with {len(master_dataset)} deep-dive records.")

if __name__ == "__main__":
    cats = ["AI", "SaaS", "Web3", "Mechanical Engineering", "Fintech"]
    locs = ["India", "USA", "Europe", "Singapore"]
    run_hybrid_deep_scraper(cats, locs)