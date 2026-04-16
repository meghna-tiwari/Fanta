from tavily import TavilyClient
from groq import Groq
import json
import re
import time

# ── Keys ──────────────────────────────────────────────
TAVILY_KEY = "tavily"
GROQ_KEY   = "groq"

tavily_client = TavilyClient(api_key=TAVILY_KEY)
groq_client   = Groq(api_key=GROQ_KEY)

# ── Load dataset ───────────────────────────────────────
with open("master_event_data.json", "r", encoding="utf-8") as f:
    MASTER_DATA = json.load(f)

print(f"Loaded {len(MASTER_DATA)} events from dataset")

# ── JSON parser (handles Groq quirks) ─────────────────
def parse_json_safely(text):
    text = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(text)
    except:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except: pass
                
        return {"error": "Healed JSON", "speakers": [], "sponsors": [], "gtm": {"status": "default"}}

# ── Core LLM call ─────────────────────────────────────
def ask_llm(system_prompt, user_prompt, retries=3):
    for attempt in range(retries):
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"  LLM attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return "{}"

# ── Get relevant events from dataset ──────────────────
def get_context(category, location, max_events=4):
    relevant = []
    for e in MASTER_DATA:
        cat_match = category.lower() in str(e.get("category", "")).lower()
        loc_match = location.lower() in str(e.get("location", "")).lower()
        content_match = category.lower() in str(e.get("raw_content", "")).lower()
        if cat_match or loc_match or content_match:
            relevant.append(e)

    # Fallback: use all data if nothing matches
    if not relevant:
        relevant = MASTER_DATA

    context = "\n\n".join([
        f"Event: {e.get('event_name', 'Unknown')}\n"
        f"Location: {e.get('location', '')}\n"
        f"Content: {str(e.get('raw_content', ''))[:400]}"
        for e in relevant[:max_events]
    ])
    return context

# ─────────────────────────────────────────────────────
# AGENTS
# ─────────────────────────────────────────────────────

def sponsor_agent(category, location):
    print("  [Sponsor Agent] running...")
    context = get_context(category, location)

    raw = ask_llm(
        system_prompt="""You are a Sponsor Agent for event planning.
Analyze past event data and recommend sponsors.
You MUST reply with ONLY a JSON object. No explanation. No markdown.
Use exactly this format:
{
  "sponsors": [
    {"name": "Company Name", "industry": "Tech", "relevance_score": 9, "reason": "why recommended"}
  ]
}""",
        user_prompt=f"""Event: {category} conference in {location}

Past events data:
{context}

Return JSON with top 5 sponsors."""
    )

    result = parse_json_safely(raw)
    print(f"  Found {len(result.get('sponsors', []))} sponsors")
    return result


def speaker_agent(category, topic):
    print("  [Speaker Agent] running...")
    context = get_context(category, category)

    raw = ask_llm(
        system_prompt="""You are a Speaker Agent for event planning.
Suggest speakers based on past events and topic.
You MUST reply with ONLY a JSON object. No explanation. No markdown.
Use exactly this format:
{
  "speakers": [
    {"name": "Person Name", "expertise": "AI/ML", "suggested_topic": "talk title", "why": "reason"}
  ]
}""",
        user_prompt=f"""Event category: {category}
Main topic: {topic}

Past events data:
{context}

Return JSON with top 5 speakers."""
    )

    result = parse_json_safely(raw)
    print(f"  Found {len(result.get('speakers', []))} speakers")
    return result


def pricing_agent(category, location, audience_size):
    print("  [Pricing Agent] running...")
    context = get_context(category, location)

    raw = ask_llm(
        system_prompt="""You are a Pricing Agent for event planning.
Predict ticket prices based on past event data.
You MUST reply with ONLY a JSON object. No explanation. No markdown.
Use exactly this format:
{
  "pricing": {
    "early_bird": 2999,
    "general": 4999,
    "vip": 9999,
    "expected_attendance": 400,
    "reasoning": "explanation here"
  }
}""",
        user_prompt=f"""Event: {category} in {location}
Target audience: {audience_size} people

Past events data:
{context}

Return JSON with ticket pricing in INR."""
    )

    result = parse_json_safely(raw)
    print(f"  Pricing done")
    return result


def venue_agent(location, audience_size, budget):
    print("  [Venue Agent] searching live venues...")

    try:
        live = tavily_client.search(
            query=f"conference venue {location} capacity {audience_size} people 2025",
            search_depth="advanced",
            max_results=3
        )
        live_context = "\n".join([
            r.get("content", "")[:300]
            for r in live.get("results", [])
        ])
    except Exception as e:
        print(f"  Tavily venue search failed: {e}")
        live_context = f"No live data. Use knowledge about venues in {location}."

    raw = ask_llm(
        system_prompt="""You are a Venue Agent for event planning.
Recommend venues based on location and requirements.
You MUST reply with ONLY a JSON object. No explanation. No markdown.
Use exactly this format:
{
  "venues": [
    {"name": "Venue Name", "city": "City", "capacity": 500, "estimated_cost": "5-8 lakhs", "why": "reason"}
  ]
}""",
        user_prompt=f"""Requirements:
- Location: {location}
- Audience: {audience_size} people
- Budget: {budget}

Web data:
{live_context}

Return JSON with top 3 venues."""
    )

    result = parse_json_safely(raw)
    print(f"  Found {len(result.get('venues', []))} venues")
    return result


def gtm_agent(category, location):
    print("  [GTM Agent] running...")

    raw = ask_llm(
        system_prompt="""You are a GTM (Go-to-Market) Agent for event planning.
Suggest communities and promotion strategies.
You MUST reply with ONLY a JSON object. No explanation. No markdown.
Use exactly this format:
{
  "gtm": {
    "discord_communities": ["community1", "community2"],
    "linkedin_groups": ["group1", "group2"],
    "promotion_message": "sample message to post",
    "best_channels": ["channel1", "channel2"]
  }
}""",
        user_prompt=f"""Event: {category} conference in {location}

Where should we promote this event?
Return JSON with GTM strategy."""
    )

    result = parse_json_safely(raw)
    print(f"  GTM strategy done")
    return result


# ─────────────────────────────────────────────────────
# ORCHESTRATOR
# ─────────────────────────────────────────────────────

def orchestrator(category, location, audience_size, topic, budget):
    print(f"\n{'='*50}")
    print(f" CONFERENCE PLANNER STARTING")
    print(f" {category} | {location} | {audience_size} people")
    print(f"{'='*50}\n")

    # Run all agents
    sponsors = sponsor_agent(category, location)
    speakers = speaker_agent(category, topic)
    pricing  = pricing_agent(category, location, audience_size)
    venues   = venue_agent(location, audience_size, budget)
    gtm      = gtm_agent(category, location)

    print("\n  [Orchestrator] creating final plan...")

    raw_final = ask_llm(
        system_prompt="""You are a senior conference strategist.
Combine all agent outputs into one final plan.
You MUST reply with ONLY a JSON object. No explanation. No markdown.
Use exactly this format:
{
  "summary": "2-3 line overview",
  "top_3_sponsors": ["name1", "name2", "name3"],
  "top_3_speakers": ["name1", "name2", "name3"],
  "recommended_venue": "venue name and city",
  "ticket_pricing": {"early_bird": 0, "general": 0, "vip": 0},
  "gtm_tip": "one key promotion tip"
}""",
        user_prompt=f"""
SPONSORS:  {json.dumps(sponsors)}
SPEAKERS:  {json.dumps(speakers)}
PRICING:   {json.dumps(pricing)}
VENUES:    {json.dumps(venues)}
GTM:       {json.dumps(gtm)}

Create final conference plan JSON.
"""
    )

    final_plan = parse_json_safely(raw_final)

    # Complete output object
    full_output = {
        "input": {
            "category": category,
            "location": location,
            "audience_size": audience_size,
            "topic": topic,
            "budget": budget
        },
        "agent_outputs": {
            "sponsors": sponsors,
            "speakers": speakers,
            "pricing":  pricing,
            "venues":   venues,
            "gtm":      gtm
        },
        "final_plan": final_plan
    }

    # Save output
    with open("conference_plan.json", "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2, ensure_ascii=False)

    print("\n" + "="*50)
    print(" DONE — saved to conference_plan.json")
    print("="*50)
    print("\n FINAL PLAN:")
    print(json.dumps(final_plan, indent=2))

    return full_output


# ── RUN ────────────────────────────────────────────────
if __name__ == "__main__":
    orchestrator(
        category      = "AI",
        location      = "India",
        audience_size = 500,
        topic         = "Large Language Models",
        budget        = "50 lakhs"
    )