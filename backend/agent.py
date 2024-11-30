import os
import instructor 
import openai
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema, BaseAgentOutputSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.base.base_io_schema import BaseIOSchema

from dotenv import load_dotenv
from rich.console import Console
from rich.text import Text
from pydantic import Field


class FinanceFactsOutputSchema(BaseIOSchema):
    """
    This schema represents the output of the agent.
    The schema contains a chat response, as well as a set of followup questions
    that could potentiallly be asked by the user to learn more about finance.
    """

    chat_message: str = Field(description="The chat response to user's message.")
    followup_questions: list[str] = Field(
        description="A list of followup questions that could potentially be asked by the user to learn more about finance."
    )

load_dotenv()
from groq import Groq

#console = Console()

api_key = os.getenv("GROQ_API_KEY")
client = instructor.from_groq(Groq(api_key=api_key), mode=instructor.Mode.JSON)
model = "llama3-8b-8192"

#client = instructor.from_openai(openai.OpenAI(base_url="http://localhost:11434/v1",api_key="ollama"),mode=instructor.Mode.MD_JSON)
#model = "llama3.2:3b-instruct-q6_K"

system_prompt_generator_custom = SystemPromptGenerator(
    background=["You are a helpful agent that can only answer about Finance"],
    steps=[
        "Analyse the user's question and determine if it's about Financial data",
        "If it is, provide the answer",
        "If it is not, apologize and say that you can only provide facts about Financial data"
    ],
    output_instructions=["Your output should be factual"]
)

agent = BaseAgent(config=BaseAgentConfig(client=client, model=model,
                                         system_prompt_generator=system_prompt_generator_custom, output_schema=FinanceFactsOutputSchema))

#initial_message = "hello! how can I help you today?"

initial_message = FinanceFactsOutputSchema(
    chat_message="Come this way, what I can teach you today?",
    followup_questions=[
        "What would be India's Economic growth?"
        "What is per capital income of an Indian?"
    ]
)
agent.memory.add_message("assistant", content=initial_message)

class FinancialBOT:
    def execute_query(self, query):
        self.user_input = query
        response = agent.run(BaseAgentInputSchema(chat_message=self.user_input))
        return {"Query": self.user_input,"response" :response.chat_message, "followup": response.followup_questions}

