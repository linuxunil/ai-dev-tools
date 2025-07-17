"""
Ollama Client - Local AI model integration for AI development tools

Provides standardized system prompts and consistent model interaction
for all AI development tools with token tracking and metrics collection.
"""

import json
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from ai_dev_tools.core.metrics_collector import (
    MetricsCollector,
    MetricType,
    WorkflowType,
    get_metrics_collector,
)


class ModelSize(Enum):
    """Available Ollama model sizes"""

    SMALL = "llama3.2:1b"  # Fast, basic reasoning
    MEDIUM = "llama3.2:3b"  # Balanced speed/quality
    LARGE = "llama3.1:8b"  # High quality reasoning
    XLARGE = "llama3.1:70b"  # Maximum quality (if available)


class PromptType(Enum):
    """Types of AI development tasks"""

    CODE_ANALYSIS = "code_analysis"
    PATTERN_DETECTION = "pattern_detection"
    SAFETY_ASSESSMENT = "safety_assessment"
    IMPACT_ANALYSIS = "impact_analysis"
    CONTEXT_ANALYSIS = "context_analysis"
    SYSTEMATIC_FIX = "systematic_fix"
    VALIDATION = "validation"


@dataclass
class OllamaResponse:
    """Response from Ollama model"""

    success: bool
    content: str
    model: str
    execution_time: float
    estimated_tokens: int
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "success": self.success,
            "content": self.content,
            "model": self.model,
            "execution_time": self.execution_time,
            "estimated_tokens": self.estimated_tokens,
            "error": self.error,
        }


class OllamaClient:
    """
    Client for interacting with local Ollama models

    Provides standardized system prompts and consistent model interaction
    with automatic token estimation and metrics collection.
    """

    # Standard system prompts for different task types
    SYSTEM_PROMPTS = {
        PromptType.CODE_ANALYSIS: """You are an expert code analyzer. Analyze code for:
- Structure and patterns
- Potential issues or improvements
- Complexity assessment
- Dependencies and relationships

Respond concisely with actionable insights. Focus on facts, not opinions.""",
        PromptType.PATTERN_DETECTION: """You are a pattern detection specialist. Given code:
- Identify recurring patterns and structures
- Assess similarity between code sections
- Suggest systematic improvements
- Prioritize patterns by impact

Respond with specific, actionable pattern analysis.""",
        PromptType.SAFETY_ASSESSMENT: """You are a code safety expert. Assess code for:
- Security vulnerabilities
- Potential runtime errors
- Resource usage issues
- Breaking changes impact

Rate risk as: SAFE, MEDIUM, HIGH, or CRITICAL. Explain reasoning briefly.""",
        PromptType.IMPACT_ANALYSIS: """You are a change impact analyst. For proposed changes:
- Identify affected components
- Assess risk of breaking changes
- Suggest testing strategies
- Prioritize by impact severity

Provide clear, actionable impact assessment.""",
        PromptType.CONTEXT_ANALYSIS: """You are a codebase context expert. Analyze project structure:
- Architecture patterns and conventions
- Code organization and modularity
- Dependencies and coupling
- Complexity and maintainability

Provide structured context analysis for AI development decisions.""",
        PromptType.SYSTEMATIC_FIX: """You are a systematic fix specialist. For code improvements:
- Identify patterns suitable for automation
- Suggest consistent fix approaches
- Prioritize by impact and safety
- Provide step-by-step fix plans

Focus on systematic, repeatable improvements.""",
        PromptType.VALIDATION: """You are a code validation expert. Validate code for:
- Syntax and semantic correctness
- Adherence to best practices
- Consistency with project patterns
- Potential runtime issues

Provide clear validation results with specific recommendations.""",
    }

    def __init__(
        self,
        default_model: ModelSize = ModelSize.SMALL,
        timeout: int = 60,
        metrics_collector: Optional[MetricsCollector] = None,
    ):
        """
        Initialize Ollama client

        Args:
            default_model: Default model size to use
            timeout: Request timeout in seconds
            metrics_collector: Optional metrics collector instance
        """
        self.default_model = default_model
        self.timeout = timeout
        self.metrics_collector = metrics_collector or get_metrics_collector()

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text

        Rough estimation: ~4 characters per token for English text
        """
        return max(1, len(text) // 4)

    def _build_prompt(
        self,
        prompt_type: PromptType,
        user_prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build complete prompt with system prompt and context

        Args:
            prompt_type: Type of prompt to use
            user_prompt: User's specific prompt
            context: Optional context information

        Returns:
            Complete formatted prompt
        """
        system_prompt = self.SYSTEM_PROMPTS[prompt_type]

        # Add context if provided
        context_section = ""
        if context:
            context_section = f"\n\nContext:\n{json.dumps(context, indent=2)}\n"

        return f"{system_prompt}{context_section}\n\nTask: {user_prompt}"

    def query(
        self,
        prompt_type: PromptType,
        user_prompt: str,
        model: Optional[ModelSize] = None,
        context: Optional[Dict[str, Any]] = None,
        workflow_type: Optional[WorkflowType] = None,
    ) -> OllamaResponse:
        """
        Query Ollama model with standardized prompt

        Args:
            prompt_type: Type of AI task
            user_prompt: Specific user prompt
            model: Model size to use (default: instance default)
            context: Optional context information
            workflow_type: Workflow type for metrics tracking

        Returns:
            OllamaResponse with result and metrics
        """
        model = model or self.default_model
        full_prompt = self._build_prompt(prompt_type, user_prompt, context)

        start_time = time.time()
        estimated_input_tokens = self._estimate_tokens(full_prompt)

        try:
            # Run Ollama command
            result = subprocess.run(
                ["ollama", "run", model.value, full_prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            execution_time = time.time() - start_time

            if result.returncode == 0:
                content = result.stdout.strip()
                estimated_output_tokens = self._estimate_tokens(content)

                # Record metrics if workflow type provided
                if workflow_type:
                    self.metrics_collector.record_metric(
                        workflow_type,
                        MetricType.TOKEN_INPUT,
                        estimated_input_tokens,
                        {"model": model.value, "prompt_type": prompt_type.value},
                    )
                    self.metrics_collector.record_metric(
                        workflow_type,
                        MetricType.TOKEN_OUTPUT,
                        estimated_output_tokens,
                        {"model": model.value, "prompt_type": prompt_type.value},
                    )
                    self.metrics_collector.record_metric(
                        workflow_type,
                        MetricType.EXECUTION_TIME,
                        execution_time,
                        {"model": model.value, "prompt_type": prompt_type.value},
                    )

                return OllamaResponse(
                    success=True,
                    content=content,
                    model=model.value,
                    execution_time=execution_time,
                    estimated_tokens=estimated_input_tokens + estimated_output_tokens,
                )
            else:
                error_msg = result.stderr.strip() or "Unknown Ollama error"
                return OllamaResponse(
                    success=False,
                    content="",
                    model=model.value,
                    execution_time=execution_time,
                    estimated_tokens=estimated_input_tokens,
                    error=error_msg,
                )

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return OllamaResponse(
                success=False,
                content="",
                model=model.value,
                execution_time=execution_time,
                estimated_tokens=estimated_input_tokens,
                error=f"Timeout after {self.timeout} seconds",
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return OllamaResponse(
                success=False,
                content="",
                model=model.value,
                execution_time=execution_time,
                estimated_tokens=estimated_input_tokens,
                error=str(e),
            )

    def quick_decision(
        self,
        prompt_type: PromptType,
        decision_prompt: str,
        exit_code: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Make quick AI decision based on exit codes and minimal context

        Optimized for exit-code-first workflows where AI makes decisions
        based on tool exit codes rather than parsing full output.

        Args:
            prompt_type: Type of decision task
            decision_prompt: Specific decision prompt
            exit_code: Exit code from previous tool
            context: Optional minimal context

        Returns:
            AI decision as string
        """
        # Build context with exit code if provided
        full_context = context or {}
        if exit_code is not None:
            full_context["exit_code"] = exit_code

        # Use smallest model for quick decisions
        response = self.query(
            prompt_type=prompt_type,
            user_prompt=decision_prompt,
            model=ModelSize.SMALL,
            context=full_context,
        )

        return response.content if response.success else "ERROR"

    def is_available(self) -> bool:
        """
        Check if Ollama is available and responsive

        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """
        List available Ollama models

        Returns:
            List of available model names
        """
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                models = []
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
                return models
            else:
                return []
        except Exception:
            return []


# Global client instance
_global_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get or create global Ollama client instance"""
    global _global_client
    if _global_client is None:
        _global_client = OllamaClient()
    return _global_client


def quick_ai_decision(
    prompt_type: PromptType,
    decision_prompt: str,
    exit_code: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """Convenience function for quick AI decisions"""
    return get_ollama_client().quick_decision(
        prompt_type, decision_prompt, exit_code, context
    )
