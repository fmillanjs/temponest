"""
Cost Calculator - Calculate costs for LLM usage across providers.

Supports dynamic pricing from database with fallback to hardcoded defaults.
"""

from typing import Dict, Tuple
from decimal import Decimal


class CostCalculator:
    """Calculate costs for LLM API usage"""

    # Fallback pricing (USD per 1M tokens) - updated 2025
    DEFAULT_PRICING = {
        "claude": {
            "claude-sonnet-4-20250514": {"input": Decimal("3.00"), "output": Decimal("15.00")},
            "claude-opus-4-20250514": {"input": Decimal("15.00"), "output": Decimal("75.00")},
            "claude-haiku-4-20250514": {"input": Decimal("0.25"), "output": Decimal("1.25")},
            "default": {"input": Decimal("3.00"), "output": Decimal("15.00")},  # Sonnet default
        },
        "openai": {
            "gpt-4o": {"input": Decimal("2.50"), "output": Decimal("10.00")},
            "gpt-4-turbo": {"input": Decimal("10.00"), "output": Decimal("30.00")},
            "gpt-3.5-turbo": {"input": Decimal("0.50"), "output": Decimal("1.50")},
            "default": {"input": Decimal("2.50"), "output": Decimal("10.00")},  # GPT-4o default
        },
        "ollama": {
            "default": {"input": Decimal("0.00"), "output": Decimal("0.00")},  # Self-hosted, free
        },
    }

    def __init__(self, db_pricing: Dict[str, Dict[str, Dict[str, Decimal]]] = None):
        """
        Initialize cost calculator.

        Args:
            db_pricing: Optional pricing from database {provider: {model: {input: X, output: Y}}}
        """
        self.db_pricing = db_pricing or {}

    def calculate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculate cost for LLM usage.

        Args:
            provider: Model provider (claude, openai, ollama)
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Tuple of (input_cost_usd, output_cost_usd, total_cost_usd)
        """
        # Get pricing (DB pricing takes precedence)
        pricing = self._get_pricing(provider, model)

        # Calculate costs
        input_cost = (Decimal(input_tokens) / Decimal(1_000_000)) * pricing["input"]
        output_cost = (Decimal(output_tokens) / Decimal(1_000_000)) * pricing["output"]
        total_cost = input_cost + output_cost

        # Round to 6 decimal places (micro-dollar precision)
        return (
            input_cost.quantize(Decimal("0.000001")),
            output_cost.quantize(Decimal("0.000001")),
            total_cost.quantize(Decimal("0.000001"))
        )

    def _get_pricing(self, provider: str, model: str) -> Dict[str, Decimal]:
        """Get pricing for a specific provider/model"""
        provider_lower = provider.lower()

        # Try DB pricing first
        if provider_lower in self.db_pricing:
            if model in self.db_pricing[provider_lower]:
                return self.db_pricing[provider_lower][model]

        # Fallback to default pricing
        if provider_lower in self.DEFAULT_PRICING:
            provider_pricing = self.DEFAULT_PRICING[provider_lower]
            if model in provider_pricing:
                return provider_pricing[model]
            # Use provider default if model not found
            return provider_pricing.get("default", {"input": Decimal("0"), "output": Decimal("0")})

        # Unknown provider - return zero cost
        return {"input": Decimal("0"), "output": Decimal("0")}

    def estimate_cost(
        self,
        provider: str,
        model: str,
        estimated_tokens: int,
        input_output_ratio: float = 0.5
    ) -> Decimal:
        """
        Estimate cost before execution.

        Args:
            provider: Model provider
            model: Model name
            estimated_tokens: Estimated total tokens
            input_output_ratio: Ratio of input to output (default 0.5 = 50% input, 50% output)

        Returns:
            Estimated total cost in USD
        """
        input_tokens = int(estimated_tokens * input_output_ratio)
        output_tokens = estimated_tokens - input_tokens

        _, _, total_cost = self.calculate_cost(provider, model, input_tokens, output_tokens)
        return total_cost

    @staticmethod
    def get_provider_from_model(model: str) -> str:
        """Infer provider from model name"""
        model_lower = model.lower()

        if "claude" in model_lower:
            return "claude"
        elif "gpt" in model_lower or "davinci" in model_lower:
            return "openai"
        elif "mistral" in model_lower or "llama" in model_lower or "codellama" in model_lower:
            return "ollama"
        else:
            return "unknown"

    def format_cost(self, cost_usd: Decimal) -> str:
        """Format cost for display"""
        if cost_usd == 0:
            return "$0.00 (free)"
        elif cost_usd < Decimal("0.01"):
            # Show micro-costs
            return f"${cost_usd:.6f}"
        else:
            return f"${cost_usd:.2f}"

    def get_all_pricing(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Get all pricing info for display"""
        result = {}

        # Combine DB and default pricing
        all_providers = set(list(self.db_pricing.keys()) + list(self.DEFAULT_PRICING.keys()))

        for provider in all_providers:
            result[provider] = {}

            # Get models from both sources
            db_models = self.db_pricing.get(provider, {})
            default_models = self.DEFAULT_PRICING.get(provider, {})
            all_models = set(list(db_models.keys()) + list(default_models.keys()))

            for model in all_models:
                if model == "default":
                    continue

                pricing = self._get_pricing(provider, model)
                result[provider][model] = {
                    "input_per_1m": f"${pricing['input']:.2f}",
                    "output_per_1m": f"${pricing['output']:.2f}",
                    "source": "database" if model in db_models else "default"
                }

        return result
