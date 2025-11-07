"""
Unit tests for cost calculator.
"""

import pytest
from decimal import Decimal
from app.cost.calculator import CostCalculator


class TestCostCalculator:
    """Test suite for CostCalculator"""

    def test_calculate_cost_claude_sonnet(self):
        """Test cost calculation for Claude Sonnet"""
        calc = CostCalculator()

        input_cost, output_cost, total_cost = calc.calculate_cost(
            provider="claude",
            model="claude-sonnet-4-20250514",
            input_tokens=1000,
            output_tokens=500
        )

        # Claude Sonnet: $3/1M input, $15/1M output
        assert input_cost == Decimal("0.003000")  # 1000 * 3.00 / 1M
        assert output_cost == Decimal("0.007500")  # 500 * 15.00 / 1M
        assert total_cost == Decimal("0.010500")

    def test_calculate_cost_claude_opus(self):
        """Test cost calculation for Claude Opus"""
        calc = CostCalculator()

        input_cost, output_cost, total_cost = calc.calculate_cost(
            provider="claude",
            model="claude-opus-4-20250514",
            input_tokens=1000,
            output_tokens=500
        )

        # Claude Opus: $15/1M input, $75/1M output
        assert input_cost == Decimal("0.015000")
        assert output_cost == Decimal("0.037500")
        assert total_cost == Decimal("0.052500")

    def test_calculate_cost_claude_haiku(self):
        """Test cost calculation for Claude Haiku"""
        calc = CostCalculator()

        input_cost, output_cost, total_cost = calc.calculate_cost(
            provider="claude",
            model="claude-haiku-4-20250514",
            input_tokens=10000,
            output_tokens=5000
        )

        # Claude Haiku: $0.25/1M input, $1.25/1M output
        assert input_cost == Decimal("0.002500")
        assert output_cost == Decimal("0.006250")
        assert total_cost == Decimal("0.008750")

    def test_calculate_cost_openai_gpt4o(self):
        """Test cost calculation for GPT-4o"""
        calc = CostCalculator()

        input_cost, output_cost, total_cost = calc.calculate_cost(
            provider="openai",
            model="gpt-4o",
            input_tokens=2000,
            output_tokens=1000
        )

        # GPT-4o: $2.50/1M input, $10.00/1M output
        assert input_cost == Decimal("0.005000")
        assert output_cost == Decimal("0.010000")
        assert total_cost == Decimal("0.015000")

    def test_calculate_cost_openai_gpt35(self):
        """Test cost calculation for GPT-3.5"""
        calc = CostCalculator()

        input_cost, output_cost, total_cost = calc.calculate_cost(
            provider="openai",
            model="gpt-3.5-turbo",
            input_tokens=5000,
            output_tokens=3000
        )

        # GPT-3.5: $0.50/1M input, $1.50/1M output
        assert input_cost == Decimal("0.002500")
        assert output_cost == Decimal("0.004500")
        assert total_cost == Decimal("0.007000")

    def test_calculate_cost_ollama_free(self):
        """Test that Ollama models are free"""
        calc = CostCalculator()

        input_cost, output_cost, total_cost = calc.calculate_cost(
            provider="ollama",
            model="mistral:7b-instruct",
            input_tokens=10000,
            output_tokens=5000
        )

        # Ollama is self-hosted, free
        assert input_cost == Decimal("0.000000")
        assert output_cost == Decimal("0.000000")
        assert total_cost == Decimal("0.000000")

    def test_calculate_cost_unknown_model_uses_provider_default(self):
        """Test that unknown models fall back to provider default"""
        calc = CostCalculator()

        input_cost, output_cost, total_cost = calc.calculate_cost(
            provider="claude",
            model="claude-unknown-model",
            input_tokens=1000,
            output_tokens=500
        )

        # Should use Claude default (Sonnet): $3/1M input, $15/1M output
        assert input_cost == Decimal("0.003000")
        assert output_cost == Decimal("0.007500")
        assert total_cost == Decimal("0.010500")

    def test_calculate_cost_unknown_provider_returns_zero(self):
        """Test that unknown providers return zero cost"""
        calc = CostCalculator()

        input_cost, output_cost, total_cost = calc.calculate_cost(
            provider="unknown-provider",
            model="some-model",
            input_tokens=1000,
            output_tokens=500
        )

        assert input_cost == Decimal("0.000000")
        assert output_cost == Decimal("0.000000")
        assert total_cost == Decimal("0.000000")

    def test_calculate_cost_case_insensitive(self):
        """Test that provider names are case-insensitive"""
        calc = CostCalculator()

        input_cost1, _, total_cost1 = calc.calculate_cost(
            provider="Claude",
            model="claude-sonnet-4-20250514",
            input_tokens=1000,
            output_tokens=500
        )

        input_cost2, _, total_cost2 = calc.calculate_cost(
            provider="CLAUDE",
            model="claude-sonnet-4-20250514",
            input_tokens=1000,
            output_tokens=500
        )

        assert input_cost1 == input_cost2
        assert total_cost1 == total_cost2

    def test_calculate_cost_with_db_pricing(self):
        """Test cost calculation with database pricing overrides"""
        db_pricing = {
            "claude": {
                "claude-sonnet-4-20250514": {
                    "input": Decimal("2.50"),  # Custom price
                    "output": Decimal("12.00")  # Custom price
                }
            }
        }

        calc = CostCalculator(db_pricing=db_pricing)

        input_cost, output_cost, total_cost = calc.calculate_cost(
            provider="claude",
            model="claude-sonnet-4-20250514",
            input_tokens=1000,
            output_tokens=500
        )

        # Should use custom DB pricing
        assert input_cost == Decimal("0.002500")
        assert output_cost == Decimal("0.006000")
        assert total_cost == Decimal("0.008500")

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens"""
        calc = CostCalculator()

        input_cost, output_cost, total_cost = calc.calculate_cost(
            provider="claude",
            model="claude-sonnet-4-20250514",
            input_tokens=0,
            output_tokens=0
        )

        assert input_cost == Decimal("0.000000")
        assert output_cost == Decimal("0.000000")
        assert total_cost == Decimal("0.000000")

    def test_calculate_cost_large_numbers(self):
        """Test cost calculation with large token numbers"""
        calc = CostCalculator()

        input_cost, output_cost, total_cost = calc.calculate_cost(
            provider="claude",
            model="claude-sonnet-4-20250514",
            input_tokens=1_000_000,  # 1M tokens
            output_tokens=500_000
        )

        # 1M input * $3 + 500k output * $15
        assert input_cost == Decimal("3.000000")
        assert output_cost == Decimal("7.500000")
        assert total_cost == Decimal("10.500000")

    def test_estimate_cost_default_ratio(self):
        """Test cost estimation with default 50/50 ratio"""
        calc = CostCalculator()

        estimated_cost = calc.estimate_cost(
            provider="claude",
            model="claude-sonnet-4-20250514",
            estimated_tokens=2000
        )

        # 50% input (1000 tokens), 50% output (1000 tokens)
        # (1000 * $3 / 1M) + (1000 * $15 / 1M) = $0.018
        assert estimated_cost == Decimal("0.018000")

    def test_estimate_cost_custom_ratio(self):
        """Test cost estimation with custom input/output ratio"""
        calc = CostCalculator()

        estimated_cost = calc.estimate_cost(
            provider="claude",
            model="claude-sonnet-4-20250514",
            estimated_tokens=1000,
            input_output_ratio=0.75  # 75% input, 25% output
        )

        # 75% input (750 tokens), 25% output (250 tokens)
        # (750 * $3 / 1M) + (250 * $15 / 1M) = $0.00225 + $0.00375 = $0.006
        assert estimated_cost == Decimal("0.006000")

    def test_get_provider_from_model_claude(self):
        """Test provider inference for Claude models"""
        assert CostCalculator.get_provider_from_model("claude-sonnet-4-20250514") == "claude"
        assert CostCalculator.get_provider_from_model("Claude-Opus-4") == "claude"
        assert CostCalculator.get_provider_from_model("claude-haiku") == "claude"

    def test_get_provider_from_model_openai(self):
        """Test provider inference for OpenAI models"""
        assert CostCalculator.get_provider_from_model("gpt-4o") == "openai"
        assert CostCalculator.get_provider_from_model("gpt-3.5-turbo") == "openai"
        assert CostCalculator.get_provider_from_model("text-davinci-003") == "openai"

    def test_get_provider_from_model_ollama(self):
        """Test provider inference for Ollama models"""
        assert CostCalculator.get_provider_from_model("mistral:7b-instruct") == "ollama"
        assert CostCalculator.get_provider_from_model("llama2:13b") == "ollama"
        assert CostCalculator.get_provider_from_model("codellama:7b") == "ollama"

    def test_get_provider_from_model_unknown(self):
        """Test provider inference for unknown models"""
        assert CostCalculator.get_provider_from_model("some-unknown-model") == "unknown"
        assert CostCalculator.get_provider_from_model("") == "unknown"

    def test_format_cost_zero(self):
        """Test cost formatting for zero cost"""
        calc = CostCalculator()
        assert calc.format_cost(Decimal("0")) == "$0.00 (free)"

    def test_format_cost_micro(self):
        """Test cost formatting for micro-costs"""
        calc = CostCalculator()
        assert calc.format_cost(Decimal("0.001234")) == "$0.001234"
        assert calc.format_cost(Decimal("0.000001")) == "$0.000001"

    def test_format_cost_normal(self):
        """Test cost formatting for normal costs"""
        calc = CostCalculator()
        assert calc.format_cost(Decimal("0.05")) == "$0.05"
        assert calc.format_cost(Decimal("1.50")) == "$1.50"
        assert calc.format_cost(Decimal("100.00")) == "$100.00"

    def test_get_all_pricing_includes_all_providers(self):
        """Test that get_all_pricing returns all providers"""
        calc = CostCalculator()
        pricing = calc.get_all_pricing()

        assert "claude" in pricing
        assert "openai" in pricing
        assert "ollama" in pricing

    def test_get_all_pricing_includes_models(self):
        """Test that get_all_pricing includes models"""
        calc = CostCalculator()
        pricing = calc.get_all_pricing()

        # Check Claude models
        assert "claude-sonnet-4-20250514" in pricing["claude"]
        assert "claude-opus-4-20250514" in pricing["claude"]
        assert "claude-haiku-4-20250514" in pricing["claude"]

        # Check OpenAI models
        assert "gpt-4o" in pricing["openai"]
        assert "gpt-4-turbo" in pricing["openai"]
        assert "gpt-3.5-turbo" in pricing["openai"]

    def test_get_all_pricing_format(self):
        """Test pricing format structure"""
        calc = CostCalculator()
        pricing = calc.get_all_pricing()

        model_pricing = pricing["claude"]["claude-sonnet-4-20250514"]
        assert "input_per_1m" in model_pricing
        assert "output_per_1m" in model_pricing
        assert "source" in model_pricing
        assert model_pricing["input_per_1m"] == "$3.00"
        assert model_pricing["output_per_1m"] == "$15.00"
        assert model_pricing["source"] == "default"

    def test_get_all_pricing_with_db_override(self):
        """Test that DB pricing shows correct source"""
        db_pricing = {
            "claude": {
                "claude-sonnet-4-20250514": {
                    "input": Decimal("2.50"),
                    "output": Decimal("12.00")
                }
            }
        }

        calc = CostCalculator(db_pricing=db_pricing)
        pricing = calc.get_all_pricing()

        model_pricing = pricing["claude"]["claude-sonnet-4-20250514"]
        assert model_pricing["input_per_1m"] == "$2.50"
        assert model_pricing["output_per_1m"] == "$12.00"
        assert model_pricing["source"] == "database"

    def test_cost_precision(self):
        """Test that costs are precise to 6 decimal places"""
        calc = CostCalculator()

        input_cost, output_cost, total_cost = calc.calculate_cost(
            provider="claude",
            model="claude-haiku-4-20250514",
            input_tokens=1,
            output_tokens=1
        )

        # Very small costs should maintain precision
        assert len(str(input_cost).split('.')[-1]) <= 6
        assert len(str(output_cost).split('.')[-1]) <= 6
        assert len(str(total_cost).split('.')[-1]) <= 6
