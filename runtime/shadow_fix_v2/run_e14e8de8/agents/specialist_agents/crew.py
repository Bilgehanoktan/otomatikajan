import os
from crewai import Agent, Task, Crew, Process

from libs.observability.logging import get_logger

logger = get_logger("crewai_orchestrator")

class CrewAIOrchestrator:
    """
    Takes the structured plan from the LangGraph CEO and deploys a CrewAI team.
    """
    def __init__(self, target_agent: str, plan_context: str):
        self.target_agent = target_agent
        self.plan_context = plan_context

    def _create_agents(self):
        # We define a few standard agents that could be in our "Crew"
        # The primary agent will be the one selected by LangGraph
        
        primary_agent = Agent(
            role=self.target_agent,
            goal=f"Execute the core implementation for the plan flawlessly.",
            backstory=(
                f"You are the {self.target_agent}. "
                "You are an expert specialist assigned by the CEO to solve this specific problem. "
                "You are autonomous, highly intelligent, and write elegant code and configurations."
            ),
            verbose=True,
            allow_delegation=False
        )

        reviewer_agent = Agent(
            role="agency-code-reviewer",
            goal="Review the implemented solution for security, performance, and correctness before final approval.",
            backstory=(
                "You are a strict QA and Code Review architect. "
                "You never approve poor code. You look for edge cases."
            ),
            verbose=True,
            allow_delegation=False
        )
        
        return primary_agent, reviewer_agent

    def _create_tasks(self, primary_agent, reviewer_agent):
        execution_task = Task(
            description=(
                f"Here is the context and plan assigned to you by the CEO:\n\n{self.plan_context}\n\n"
                "1. Analyze the context.\n"
                "2. Perform the exact implementation steps required.\n"
                "3. Ensure the output is ready for production."
            ),
            expected_output="Final executed code, report, or configuration.",
            agent=primary_agent
        )

        review_task = Task(
            description=(
                "Ensure the implementation task is perfectly executed. "
                "Check for architectural flaws. If valid, approve."
            ),
            expected_output="A review report detailing either 'APPROVED' or providing feedback for iteration.",
            agent=reviewer_agent
        )

        return [execution_task, review_task]

    def run_crew(self) -> str:
        """Executes the CrewAI workflow synchronously."""
        logger.info(f"Setting up CrewAI for target agent: {self.target_agent}")
        
        primary_agent, reviewer_agent = self._create_agents()
        tasks = self._create_tasks(primary_agent, reviewer_agent)
        
        crew = Crew(
            agents=[primary_agent, reviewer_agent],
            tasks=tasks,
            process=Process.sequential, # Execute sequentially: Code -> Review
            verbose=True
        )
        
        logger.info("CrewAI execution kicked off.")
        try:
            # We mock the usage here to avoid needing to parse real LLM tokens immediately during testing,
            # but in production this triggers real LLM chains.
            result = crew.kickoff()
            logger.info("CrewAI execution finished successfully.")
            return str(result)
        except Exception as e:
            logger.error(f"CrewAI mapping failed: {e}")
            return f"Error executing CrewAI: {str(e)}"
