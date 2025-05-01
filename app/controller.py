import asyncio
from typing import Dict, List, Tuple, Any, Optional
from app.agents import sentiment
from app.agents.base import BaseAgent, AgentOutput, AgentResponse
from app.agents.sentiment import SentimentAgent
from app.agents.toxicity import ToxicityAgent
from app.agents.hate_speech import HateSpeechAgent
from app.config import settings
from app.logger import get_logger
import time

logger = get_logger()


class AgentController:
    """Manages loading, running, and aggregating results from multiple agents."""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self._load_agents()

    def _load_agents(self):
        """Initializes and stores agent instances."""
        # TODO: Make this dynamic, potentially loading from config.yaml (REQ-027)
        agent_classes = {
            "sentiment": SentimentAgent,
            "toxicity": ToxicityAgent,
            "hate_speech": HateSpeechAgent,
        }
        model_ids = {
            "sentiment": settings.SENTIMENT_MODEL_ID,
            "toxicity": settings.TOXICITY_MODEL_ID,
            "hate_speech": settings.HATE_SPEECH_MODEL_ID,
        }

        for name, AgentClass in agent_classes.items():
            try:
                start_time = time.time()
                model_id = model_ids.get(name)
                if not model_id:
                    logger.warning(f"Model ID not found for agent '{name}' in settings. Skipping.")
                    continue
                logger.info(f"Loading agent '{name}' with model '{model_id}'...")
                self.agents[name] = AgentClass(model_id=model_id)
                # Basic warm-up during load (REQ-009)``
                self.agents[name].predict("warmup")
                load_time = time.time() - start_time
                logger.info(f"Agent '{name}' loaded and warmed up in {load_time:.2f} seconds.")
            except Exception as e:
                logger.error(f"Failed to load agent '{name}': {e}", exc_info=True)

    async def analyze(self, text: str) -> Tuple[Dict[str, AgentOutput], float]:
        """Runs all registered agents concurrently on the input text."""
        start_time = time.time()
        tasks = []
        agent_names = list(self.agents.keys())

        # Create async tasks for each agent's prediction (REQ-020)
        for agent_name in agent_names:
            agent = self.agents[agent_name]
            tasks.append(self._run_agent_predict(agent, text))

        # Gather results concurrently
        raw_results: List[Any] = await asyncio.gather(*tasks, return_exceptions=True)
        latency = time.time() - start_time
        logger.debug(f"All agents completed in {latency:.4f} seconds.")

        # Process results and normalize
        analysis_details: Dict[str, AgentOutput] = {}
        for i, result in enumerate(raw_results):
            agent_name = agent_names[i]
            if isinstance(result, Exception):
                logger.error(f"Agent '{agent_name}' failed during prediction: {result}")
                # Optionally include error state in response
                # analysis_details[agent_name] = AgentOutput(label="ERROR", score=0.0)
            elif isinstance(result, AgentResponse):
                # Directly use the AgentResponse fields if normalization is not needed here
                analysis_details[agent_name] = AgentOutput(label=result.label, score=result.confidence)
            else:
                logger.warning(f"Agent '{agent_name}' returned unexpected result type: {type(result)}")

        return analysis_details, latency

    async def _run_agent_predict(self, agent: BaseAgent, text: str) -> AgentResponse:
        """Helper to run agent prediction, potentially in a thread pool if needed."""
        # If agent.predict is blocking CPU-bound code, run in a thread pool:
        # loop = asyncio.get_running_loop()
        # return await loop.run_in_executor(None, agent.predict, text)
        # For now, assume predict is I/O bound or fast enough for direct await
        # Since agent.predict is synchronous, we call it directly.
        # The async def wrapper makes this function awaitable for asyncio.gather.
        return agent.predict(text)  # Remove await, agent.predict is synchronous

    def aggregate_decision(self, analysis_details: Dict[str, AgentOutput]) -> Tuple[str, List[str]]:
        """Applies ensemble logic to agent outputs to make a final decision."""
        # TODO: Make thresholds configurable (REQ-012)
        flagged_reasons = []
        decision = "safe"
        # Define thresholds (consider moving to config or constants)
        toxicity_threshold = 0.7
        hate_speech_threshold = 0.7
        sentiment_threshold = 0.7

        toxicity_result = analysis_details.get("toxicity")
        hate_speech_result = analysis_details.get("hate_speech")
        sentiment_result = analysis_details.get("sentiment")

        # Check toxicity score against threshold
        if toxicity_result and toxicity_result.score > toxicity_threshold:
            flagged_reasons.append(f"High toxicity score: {toxicity_result.score:.2f}")
            decision = "flagged"

        # Check hate speech score against threshold
        if hate_speech_result and hate_speech_result.score > hate_speech_threshold:
            flagged_reasons.append(f"High hate speech score: {hate_speech_result.score:.2f}")
            decision = "flagged"

        if (
            sentiment_result
            and ("very_negative" == sentiment_result.label)
            and sentiment_result.score > sentiment_threshold
        ):
            flagged_reasons.append(f"High negative sentiment score: {sentiment_result.score:.2f}")
            decision = "flagged"

        # TODO: Add more complex ensemble logic if needed (REQ-013)
        # Example: Consider sentiment if toxicity is borderline, etc.

        if not flagged_reasons and decision == "safe":
            logger.info(f"Input text classified as '{decision}'. Details: {analysis_details}")
        else:
            logger.warning(
                f"Input text classified as '{decision}'. Reasons: {'; '.join(flagged_reasons)}. Details: {analysis_details}"
            )

        return decision, flagged_reasons

    def get_available_models(self) -> List[Dict[str, str]]:
        """Returns metadata for all loaded agents."""
        return [agent.get_metadata() for agent in self.agents.values()]

    def health_check(self) -> Dict[str, bool]:
        """Checks the health of all registered agents."""
        health_status = {}
        for name, agent in self.agents.items():
            health_status[name] = agent.health_check()
            logger.debug(f"Agent '{name}' health check: {'OK' if health_status[name] else 'FAIL'}")
        return health_status


# Instantiate the controller globally. Agents are loaded here.
agent_controller = AgentController()
