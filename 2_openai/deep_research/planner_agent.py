from pydantic import BaseModel, Field
from agents import Agent


HOW_MANY_SEARCHES = 5


INSTRUCTIONS = f"You're a helpful research assistant.\
    Given a research query, come up with a set of web searches to perform to best answer the query.\
        Output {HOW_MANY_SEARCHES} terms to query for"


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for this search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description=f"A list of web searches to perform to best answer the query.")

planner_agent = Agent(name='Planner Agent',
                      instructions=INSTRUCTIONS,
                      model="gpt-4o-mini",
                      output_type=WebSearchPlan)

