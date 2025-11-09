"""
Unit tests for Designer Agent.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from app.agents.designer import DesignerAgent


class TestDesignerAgent:
    """Test suite for DesignerAgent"""

    @pytest.fixture
    def mock_rag_memory(self):
        """Create mock RAG memory"""
        mock = AsyncMock()
        mock.retrieve = AsyncMock(return_value=[
            {
                "source": "docs/design/material-design.md",
                "version": "v3.0",
                "score": 0.95,
                "content": "Material Design 3 button patterns with accessibility"
            },
            {
                "source": "docs/design/tailwind-ui.md",
                "version": "v2.0",
                "score": 0.88,
                "content": "Tailwind CSS component examples"
            }
        ])
        return mock

    @pytest.fixture
    def mock_tracer(self):
        """Create mock Langfuse tracer"""
        mock = Mock()
        mock.start_trace = Mock(return_value={"id": "trace-123"})
        mock.end_trace = Mock()
        return mock

    @pytest.fixture
    def designer_agent(self, mock_rag_memory, mock_tracer):
        """Create DesignerAgent instance with mocked dependencies"""
        with patch('app.agents.designer.Agent'):
            agent = DesignerAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="test-model",
                temperature=0.3,
                top_p=0.9,
                max_tokens=3072,
                seed=42
            )
            return agent

    def test_init_default_params(self, mock_rag_memory, mock_tracer):
        """Test DesignerAgent initialization with default parameters"""
        with patch('app.agents.designer.Agent'):
            agent = DesignerAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="test-model"
            )

            assert agent.code_model == "test-model"
            assert agent.temperature == 0.3  # Higher for creative design
            assert agent.top_p == 0.9
            assert agent.max_tokens == 3072  # Higher for design docs
            assert agent.seed == 42

    def test_init_custom_params(self, mock_rag_memory, mock_tracer):
        """Test DesignerAgent initialization with custom parameters"""
        with patch('app.agents.designer.Agent'):
            agent = DesignerAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="custom-model",
                temperature=0.5,
                top_p=0.95,
                max_tokens=4096,
                seed=100
            )

            assert agent.code_model == "custom-model"
            assert agent.temperature == 0.5
            assert agent.top_p == 0.95
            assert agent.max_tokens == 4096
            assert agent.seed == 100

    def test_create_search_design_patterns_tool(self, designer_agent):
        """Test search design patterns tool creation"""
        tool = designer_agent._create_search_design_patterns_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    @pytest.mark.asyncio
    async def test_search_design_patterns_with_results(self, designer_agent, mock_rag_memory):
        """Test search design patterns tool returns formatted results"""
        tool = designer_agent._create_search_design_patterns_tool()

        result = await tool.func("button patterns")

        # Verify RAG was called
        mock_rag_memory.retrieve.assert_called_once_with(
            query="design pattern: button patterns",
            top_k=5,
            min_score=0.7
        )

        # Verify result format
        assert "[Design Pattern 1]" in result
        assert "[Design Pattern 2]" in result
        assert "docs/design/material-design.md" in result
        assert "v3.0" in result
        assert "0.95" in result

    @pytest.mark.asyncio
    async def test_search_design_patterns_no_results(self, designer_agent):
        """Test search design patterns tool when no results found"""
        designer_agent.rag_memory.retrieve = AsyncMock(return_value=[])
        tool = designer_agent._create_search_design_patterns_tool()

        result = await tool.func("unknown pattern")

        assert "No design patterns found" in result
        assert "Material Design 3" in result or "Tailwind CSS" in result

    def test_create_generate_color_palette_tool(self, designer_agent):
        """Test generate color palette tool creation"""
        tool = designer_agent._create_generate_color_palette_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_generate_color_palette_light_theme(self, designer_agent):
        """Test color palette generation for light theme"""
        tool = designer_agent._create_generate_color_palette_tool()

        result = tool.func("#3B82F6", "light")

        # Verify palette structure
        assert "#3B82F6" in result  # Brand color
        assert "brand" in result
        assert "primary" in result
        assert "semantic" in result
        assert "success" in result
        assert "warning" in result
        assert "error" in result
        assert "neutral" in result
        assert "WCAG" in result

    def test_generate_color_palette_dark_theme(self, designer_agent):
        """Test color palette generation for dark theme"""
        tool = designer_agent._create_generate_color_palette_tool()

        result = tool.func("#10B981", "dark")

        # Verify palette includes dark theme considerations
        assert "#10B981" in result
        assert "dark" in result.lower()
        assert "WCAG" in result

    def test_generate_color_palette_contains_semantic_colors(self, designer_agent):
        """Test generated palette includes all semantic colors"""
        tool = designer_agent._create_generate_color_palette_tool()

        result = tool.func("#FF5733", "light")

        # Check semantic colors
        assert "#10B981" in result  # Success (green)
        assert "#F59E0B" in result  # Warning (amber)
        assert "#EF4444" in result  # Error (red)
        assert "#3B82F6" in result  # Info (blue)

    def test_generate_color_palette_neutral_scale(self, designer_agent):
        """Test generated palette includes full neutral scale"""
        tool = designer_agent._create_generate_color_palette_tool()

        result = tool.func("#6366F1", "light")

        # Verify 10-shade neutral scale
        for shade in ["50", "100", "200", "300", "400", "500", "600", "700", "800", "900"]:
            assert shade in result

    def test_create_validate_accessibility_tool(self, designer_agent):
        """Test validate accessibility tool creation"""
        tool = designer_agent._create_validate_accessibility_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_validate_accessibility_wcag_checklist(self, designer_agent):
        """Test accessibility validation includes WCAG checklist"""
        tool = designer_agent._create_validate_accessibility_tool()

        result = tool.func("design specification")

        # Verify WCAG checklist categories
        assert "Color Contrast" in result
        assert "Keyboard Navigation" in result
        assert "Semantic HTML" in result
        assert "ARIA" in result
        assert "Touch Targets" in result
        assert "4.5:1" in result  # Normal text contrast
        assert "3:1" in result  # Large text/UI contrast

    def test_validate_accessibility_button_recommendations(self, designer_agent):
        """Test accessibility validation for button components"""
        tool = designer_agent._create_validate_accessibility_tool()

        result = tool.func("button component with primary and secondary variants")

        assert "button" in result.lower()
        assert "44×44px" in result or "44px" in result  # Minimum touch target

    def test_validate_accessibility_form_recommendations(self, designer_agent):
        """Test accessibility validation for form inputs"""
        tool = designer_agent._create_validate_accessibility_tool()

        result = tool.func("form with input fields and labels")

        assert "label" in result.lower()
        assert "input" in result.lower() or "form" in result.lower()

    def test_validate_accessibility_modal_recommendations(self, designer_agent):
        """Test accessibility validation for modal dialogs"""
        tool = designer_agent._create_validate_accessibility_tool()

        result = tool.func("modal dialog for user confirmation")

        assert "dialog" in result.lower()
        assert "ESC" in result or "focus" in result.lower()

    def test_validate_accessibility_navigation_recommendations(self, designer_agent):
        """Test accessibility validation for navigation"""
        tool = designer_agent._create_validate_accessibility_tool()

        result = tool.func("navigation menu with dropdowns")

        assert "nav" in result.lower()
        assert "aria-label" in result

    def test_validate_accessibility_icon_recommendations(self, designer_agent):
        """Test accessibility validation for icons"""
        tool = designer_agent._create_validate_accessibility_tool()

        result = tool.func("icon buttons for actions")

        assert "icon" in result.lower()
        assert "aria-label" in result or "sr-only" in result

    def test_create_generate_design_tokens_tool(self, designer_agent):
        """Test generate design tokens tool creation"""
        tool = designer_agent._create_generate_design_tokens_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_generate_design_tokens_json_format(self, designer_agent):
        """Test design tokens generation in JSON format"""
        tool = designer_agent._create_generate_design_tokens_tool()

        result = tool.func("json")

        # Verify JSON structure
        assert "spacing" in result
        assert "fontSize" in result
        assert "fontWeight" in result
        assert "borderRadius" in result
        assert "boxShadow" in result
        assert "breakpoints" in result
        assert "0.25rem" in result  # 4px spacing
        assert "1rem" in result  # 16px base

    def test_generate_design_tokens_css_format(self, designer_agent):
        """Test design tokens generation in CSS format"""
        tool = designer_agent._create_generate_design_tokens_tool()

        result = tool.func("css")

        # Verify CSS custom properties
        assert ":root" in result
        assert "--spacing-" in result
        assert "--fontSize-" in result
        assert "--fontWeight-" in result
        assert "--borderRadius-" in result
        assert "var(--" in result  # Usage example

    def test_generate_design_tokens_tailwind_format(self, designer_agent):
        """Test design tokens generation in Tailwind format"""
        tool = designer_agent._create_generate_design_tokens_tool()

        result = tool.func("tailwind")

        # Verify Tailwind config
        assert "tailwind.config.js" in result
        assert "module.exports" in result
        assert "theme" in result
        assert "extend" in result

    def test_generate_design_tokens_invalid_format(self, designer_agent):
        """Test design tokens with invalid format"""
        tool = designer_agent._create_generate_design_tokens_tool()

        result = tool.func("invalid")

        assert "Invalid format" in result
        assert "json" in result
        assert "css" in result
        assert "tailwind" in result

    def test_generate_design_tokens_spacing_scale(self, designer_agent):
        """Test design tokens include proper spacing scale"""
        tool = designer_agent._create_generate_design_tokens_tool()

        result = tool.func("json")

        # Verify 4px base grid system
        assert "0.25rem" in result  # 4px
        assert "0.5rem" in result   # 8px
        assert "1rem" in result      # 16px
        assert "1.5rem" in result    # 24px

    def test_create_create_component_spec_tool(self, designer_agent):
        """Test create component spec tool creation"""
        tool = designer_agent._create_create_component_spec_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_create_component_spec_button(self, designer_agent):
        """Test component spec generation for button"""
        tool = designer_agent._create_create_component_spec_tool()

        result = tool.func("PrimaryButton", "button")

        # Verify button spec
        assert "PrimaryButton" in result
        assert "Primary" in result
        assert "Secondary" in result
        assert "Ghost" in result  # Three variants
        assert "Hover" in result
        assert "Focus" in result
        assert "Active" in result
        assert "Disabled" in result  # All states
        assert "44×44px" in result or "44px" in result  # Minimum size
        assert "aria-label" in result  # Accessibility

    def test_create_component_spec_input(self, designer_agent):
        """Test component spec generation for input"""
        tool = designer_agent._create_create_component_spec_tool()

        result = tool.func("EmailInput", "input")

        # Verify input spec
        assert "EmailInput" in result
        assert "Text Input" in result or "input" in result.lower()
        assert "44px" in result  # Minimum height
        assert "label" in result.lower()
        assert "aria-describedby" in result
        assert "aria-invalid" in result
        assert "aria-required" in result

    def test_create_component_spec_card(self, designer_agent):
        """Test component spec generation for card"""
        tool = designer_agent._create_create_component_spec_tool()

        result = tool.func("ProductCard", "card")

        # Verify card spec
        assert "ProductCard" in result
        assert "Elevated" in result
        assert "Outlined" in result
        assert "shadow" in result.lower()
        assert "article" in result or "section" in result

    def test_create_component_spec_modal(self, designer_agent):
        """Test component spec generation for modal"""
        tool = designer_agent._create_create_component_spec_tool()

        result = tool.func("ConfirmDialog", "modal")

        # Verify modal spec
        assert "ConfirmDialog" in result
        assert "Backdrop" in result
        assert "Dialog" in result
        assert "dialog" in result.lower()
        assert "aria-modal" in result
        assert "ESC" in result
        assert "focus trap" in result.lower() or "Focus trap" in result
        # Note: handleClose is example code, not a template variable

    def test_create_component_spec_default_to_button(self, designer_agent):
        """Test component spec defaults to button for unknown type"""
        tool = designer_agent._create_create_component_spec_tool()

        result = tool.func("CustomComponent", "unknown")

        # Should default to button spec
        assert "CustomComponent" in result
        assert "button" in result.lower() or "Primary" in result

    def test_extract_citations_with_matches(self, designer_agent):
        """Test citation extraction from result"""
        result_text = """
[Design Pattern 1] Material Design Buttons (v3.0)
[Design Pattern 2] Tailwind UI Components (v2.1)
[Citation 3] WCAG Guidelines (v2.1)
"""

        citations = designer_agent._extract_citations(result_text)

        assert len(citations) >= 2
        assert citations[0]["source"] == "Material Design Buttons"
        assert citations[0]["version"] == "3.0"
        assert citations[1]["source"] == "Tailwind UI Components"
        assert citations[1]["version"] == "2.1"

    def test_extract_citations_no_matches(self, designer_agent):
        """Test citation extraction with no citations"""
        result_text = "No citations in this text"

        citations = designer_agent._extract_citations(result_text)

        assert len(citations) == 0

    def test_extract_citations_limit_to_five(self, designer_agent):
        """Test citation extraction limits to 5 citations"""
        result_text = """
[Design Pattern 1] Source1 (v1.0)
[Design Pattern 2] Source2 (v2.0)
[Design Pattern 3] Source3 (v3.0)
[Design Pattern 4] Source4 (v4.0)
[Design Pattern 5] Source5 (v5.0)
[Design Pattern 6] Source6 (v6.0)
[Design Pattern 7] Source7 (v7.0)
"""

        citations = designer_agent._extract_citations(result_text)

        assert len(citations) == 5

    def test_extract_section(self, designer_agent):
        """Test section extraction from result"""
        result_text = """
Some intro text.

Wireframe:
This is the wireframe content
that spans multiple lines.

Some other section.
"""

        section = designer_agent._extract_section(result_text, "wireframe")

        assert "wireframe content" in section.lower()
        assert "multiple lines" in section.lower()

    def test_extract_section_case_insensitive(self, designer_agent):
        """Test section extraction is case insensitive"""
        result_text = """
DESIGN TOKENS:
Token content here.

Other content.
"""

        section = designer_agent._extract_section(result_text, "design tokens")

        assert "Token content" in section

    def test_extract_section_not_found(self, designer_agent):
        """Test section extraction when section not found"""
        result_text = "Some text without the section"

        section = designer_agent._extract_section(result_text, "missing section")

        assert section == ""

    def test_extract_code_html(self, designer_agent):
        """Test HTML code extraction"""
        result_text = """
Some text before.

```html
<div class="container">
  <h1>Hello</h1>
</div>
```

Some text after.
"""

        code = designer_agent._extract_code(result_text, "html")

        assert "<div class=\"container\">" in code
        assert "<h1>Hello</h1>" in code

    def test_extract_code_jsx(self, designer_agent):
        """Test JSX code extraction"""
        result_text = """
```jsx
<Button variant="primary">
  Click me
</Button>
```
"""

        code = designer_agent._extract_code(result_text, "jsx")

        assert "Button variant=\"primary\"" in code
        assert "Click me" in code

    def test_extract_code_css(self, designer_agent):
        """Test CSS code extraction"""
        result_text = """
```css
.button {
  padding: 1rem;
  border-radius: 0.5rem;
}
```
"""

        code = designer_agent._extract_code(result_text, "css")

        assert ".button" in code
        assert "padding: 1rem" in code

    def test_extract_code_not_found(self, designer_agent):
        """Test code extraction when code block not found"""
        result_text = "Some text without code blocks"

        code = designer_agent._extract_code(result_text, "python")

        assert code == ""

    def test_extract_code_case_insensitive(self, designer_agent):
        """Test code extraction is case insensitive"""
        result_text = """
```HTML
<div>Content</div>
```
"""

        code = designer_agent._extract_code(result_text, "html")

        assert "<div>Content</div>" in code

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_rag_memory, mock_tracer):
        """Test successful designer agent execution"""
        with patch('app.agents.designer.Agent') as mock_agent_class:
            with patch('app.agents.designer.Crew') as mock_crew_class:
                with patch('app.agents.designer.Task') as mock_task_class:
                    designer_agent = DesignerAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    # Mock crew execution
                    mock_crew = MagicMock()
                    mock_crew.kickoff_async = AsyncMock(return_value="""Design System:
[Design Pattern 1] Material Design (v3.0)

wireframe:
Component layout here.


```html
<button>Click</button>
```

```css
.button { padding: 1rem; }
```""")
                    mock_crew_class.return_value = mock_crew

                    result = await designer_agent.execute(
                        task="Create a button design",
                        context={"brand_color": "#3B82F6"},
                        task_id="task-123"
                    )

                    assert "design" in result
                    assert "accessibility" in result
                    assert "implementation" in result
                    assert "citations" in result
                    assert "execution_time_ms" in result
                    assert isinstance(result["execution_time_ms"], int)

                    # Verify tracer was called
                    mock_tracer.start_trace.assert_called_once()
                    mock_tracer.end_trace.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_error_handling(self, mock_rag_memory, mock_tracer):
        """Test error handling during execution"""
        with patch('app.agents.designer.Agent') as mock_agent_class:
            with patch('app.agents.designer.Crew') as mock_crew_class:
                with patch('app.agents.designer.Task') as mock_task_class:
                    designer_agent = DesignerAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    # Mock crew execution failure
                    mock_crew_class.side_effect = Exception("Design generation failed")

                    with pytest.raises(Exception, match="Design generation failed"):
                        await designer_agent.execute(
                            task="Create design",
                            context={},
                            task_id="task-error"
                        )

                    # Verify error was traced
                    mock_tracer.start_trace.assert_called_once()
                    mock_tracer.end_trace.assert_called_once()
                    call_args = mock_tracer.end_trace.call_args
                    assert "error" in call_args[1]["output"]
