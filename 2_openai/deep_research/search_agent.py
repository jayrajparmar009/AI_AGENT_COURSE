from agents import Agent, WebSearchTool, ModelSettings


INSTRUCTIONS = (
    "You're a research assistant. Given a search term, you search the web for that term and"
    "produce a consice summary of the most relevant information you found. The summary must be 2-3 paragraphs long and less than 300 words."
    "Capture key facts, write succintly and no need to have complete sentences or perfect grammar."
    "This will be used by another agent to write a report, so focus on factual information and avoid fluff."
    "Do not include additional commentary other than summary itself."
)

search_agent = Agent(name = 'Search Agent',
                     instructions=INSTRUCTIONS,
                     tools=[WebSearchTool(search_context_size="low")],
                     model = "gpt-4o-mini",
                     model_settings=ModelSettings(tool_choice='required')
                     )