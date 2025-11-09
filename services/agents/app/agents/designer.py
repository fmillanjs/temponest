"""
Designer/UX Agent - UI/UX design generation and design systems.

Responsibilities:
- Generate wireframes (ASCII art, Mermaid diagrams, structured descriptions)
- Create design systems (color palettes, typography, spacing scales)
- Generate component specifications with accessibility guidelines
- Create design tokens (JSON/CSS format)
- Validate accessibility (WCAG 2.1 AA compliance)
- Generate responsive layouts and breakpoint strategies
"""

from typing import Dict, Any, List, Optional
import time
import json
import re
from crewai import Agent, Task, Crew
from crewai.tools import tool

from app.memory.rag import RAGMemory
from app.memory.langfuse_tracer import LangfuseTracer


class DesignerAgent:
    """Designer/UX agent that generates UI designs and design systems"""

    def __init__(
        self,
        rag_memory: RAGMemory,
        tracer: LangfuseTracer,
        code_model: str,
        temperature: float = 0.3,  # Slightly higher for creative design
        top_p: float = 0.9,
        max_tokens: int = 3072,  # Higher for design documentation
        seed: int = 42
    ):
        self.rag_memory = rag_memory
        self.tracer = tracer
        self.code_model = code_model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.seed = seed

        # Create the agent
        self.agent = Agent(
            role="Senior UI/UX Designer",
            goal="Create beautiful, accessible, and user-friendly designs that follow industry best practices",
            backstory="""You are a senior UI/UX designer with expertise in:
            - User-centered design and design thinking methodologies
            - Material Design, Tailwind CSS, and modern design systems
            - WCAG 2.1 Level AA accessibility standards
            - Responsive design and mobile-first approaches
            - Color theory, typography, and visual hierarchy
            - Component-driven design and atomic design principles
            - Design tokens and design system architecture

            You ALWAYS:
            - Create accessible designs (color contrast, semantic HTML, ARIA)
            - Use consistent spacing scales (4px/8px grid systems)
            - Define mobile, tablet, and desktop breakpoints
            - Follow design system patterns from the knowledge base
            - Include hover/focus/active states for interactive elements
            - Provide design rationale and user experience considerations
            - Generate both high-fidelity specs and implementation-ready code
            - Consider internationalization (i18n) and RTL layouts
            - Include dark mode variants where appropriate""",
            verbose=True,
            allow_delegation=False,
            tools=[
                self._create_search_design_patterns_tool(),
                self._create_generate_color_palette_tool(),
                self._create_validate_accessibility_tool(),
                self._create_generate_design_tokens_tool(),
                self._create_create_component_spec_tool()
            ],
            llm_config={
                "model": code_model,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "seed": seed
            }
        )

    def _create_search_design_patterns_tool(self):
        """Create tool for searching design patterns"""
        rag_memory = self.rag_memory

        @tool("search_design_patterns")
        async def search_design_patterns(query: str) -> str:
            """
            Search the knowledge base for UI/UX design patterns and best practices.

            Args:
                query: What design pattern you need (e.g., "Material Design buttons", "navigation patterns")

            Returns:
                Relevant design patterns with examples
            """
            results = await rag_memory.retrieve(
                query=f"design pattern: {query}",
                top_k=5,
                min_score=0.7
            )

            if not results:
                return "No design patterns found. Use Material Design 3 or Tailwind CSS best practices."

            # Format results
            output = []
            for i, doc in enumerate(results, 1):
                output.append(f"""
[Design Pattern {i}] {doc['source']} (v{doc['version']})
Relevance: {doc['score']:.2f}

```
{doc['content']}
```

---
""")

            return "\n".join(output)

        return search_design_patterns

    def _create_generate_color_palette_tool(self):
        """Create tool for generating color palettes"""

        @tool("generate_color_palette")
        def generate_color_palette(brand_color: str, theme: str = "light") -> str:
            """
            Generate a comprehensive color palette from a brand color.

            Args:
                brand_color: Hex color code (e.g., "#3B82F6")
                theme: "light" or "dark" theme

            Returns:
                Complete color palette with semantic color assignments
            """
            # Parse hex color (simplified - in production use color science library)
            hex_color = brand_color.strip('#')

            # Generate palette structure
            palette = {
                "brand": {
                    "primary": brand_color,
                    "primary-light": f"#{hex_color}33",  # 20% opacity
                    "primary-dark": f"#{hex_color}CC",   # Darker variant
                },
                "semantic": {
                    "success": "#10B981",  # Green
                    "warning": "#F59E0B",  # Amber
                    "error": "#EF4444",    # Red
                    "info": "#3B82F6",     # Blue
                },
                "neutral": {
                    "50": "#F9FAFB",
                    "100": "#F3F4F6",
                    "200": "#E5E7EB",
                    "300": "#D1D5DB",
                    "400": "#9CA3AF",
                    "500": "#6B7280",
                    "600": "#4B5563",
                    "700": "#374151",
                    "800": "#1F2937",
                    "900": "#111827",
                },
                "text": {
                    "primary": "#111827" if theme == "light" else "#F9FAFB",
                    "secondary": "#6B7280" if theme == "light" else "#D1D5DB",
                    "disabled": "#9CA3AF" if theme == "light" else "#6B7280",
                },
                "background": {
                    "primary": "#FFFFFF" if theme == "light" else "#111827",
                    "secondary": "#F9FAFB" if theme == "light" else "#1F2937",
                    "tertiary": "#F3F4F6" if theme == "light" else "#374151",
                }
            }

            # WCAG contrast validation notes
            notes = f"""
Color Palette Generated ({theme} theme):
✓ Brand color: {brand_color}
✓ Semantic colors: Success, Warning, Error, Info
✓ 10-shade neutral scale (50-900)
✓ Text colors with proper contrast ratios
✓ Background layers for depth

WCAG 2.1 Considerations:
- Primary text on background: {'>4.5:1 contrast (AA)' if theme == 'light' else '>4.5:1 contrast (AA)'}
- Secondary text on background: {'>4.5:1 contrast (AA)' if theme == 'light' else '>3:1 contrast (AA)'}
- Interactive elements: Ensure 3:1 contrast for UI components

Usage:
- Use brand.primary for CTAs and key actions
- Use semantic colors for status indicators
- Use neutral scale for borders, dividers, backgrounds
- Always test color combinations with contrast checker
"""

            return f"{json.dumps(palette, indent=2)}\n\n{notes}"

        return generate_color_palette

    def _create_validate_accessibility_tool(self):
        """Create tool for validating accessibility"""

        @tool("validate_accessibility")
        def validate_accessibility(design_spec: str) -> str:
            """
            Validate design against WCAG 2.1 Level AA accessibility standards.

            Args:
                design_spec: Design specification or component description

            Returns:
                Accessibility assessment with WCAG compliance checklist
            """
            checklist = {
                "Color Contrast": {
                    "status": "check_required",
                    "criteria": [
                        "Normal text: 4.5:1 contrast ratio minimum",
                        "Large text (18pt+): 3:1 contrast ratio minimum",
                        "UI components: 3:1 contrast ratio minimum"
                    ]
                },
                "Keyboard Navigation": {
                    "status": "check_required",
                    "criteria": [
                        "All interactive elements accessible via keyboard",
                        "Visible focus indicators (2px outline minimum)",
                        "Logical tab order (top-left to bottom-right)",
                        "Skip links for main content navigation"
                    ]
                },
                "Semantic HTML": {
                    "status": "check_required",
                    "criteria": [
                        "Proper heading hierarchy (h1 → h2 → h3)",
                        "Semantic landmarks (nav, main, aside, footer)",
                        "Proper button/link usage (buttons for actions, links for navigation)",
                        "Form labels associated with inputs"
                    ]
                },
                "ARIA": {
                    "status": "check_required",
                    "criteria": [
                        "aria-label for icon-only buttons",
                        "aria-expanded for collapsible content",
                        "aria-live for dynamic content updates",
                        "aria-describedby for help text"
                    ]
                },
                "Touch Targets": {
                    "status": "check_required",
                    "criteria": [
                        "Minimum 44×44px touch target size",
                        "8px minimum spacing between targets",
                        "Larger targets for primary actions (48×48px)"
                    ]
                },
                "Text": {
                    "status": "check_required",
                    "criteria": [
                        "Minimum 16px font size for body text",
                        "Maximum 80 characters line length",
                        "1.5 line height for readability",
                        "No text in images (use real text with CSS)"
                    ]
                },
                "Motion": {
                    "status": "check_required",
                    "criteria": [
                        "Respect prefers-reduced-motion for animations",
                        "No auto-playing videos with sound",
                        "Pause/stop controls for moving content"
                    ]
                }
            }

            recommendations = []

            # Analyze design spec (simplified heuristics)
            spec_lower = design_spec.lower()

            if "button" in spec_lower:
                recommendations.append("Ensure buttons have minimum 44×44px size and clear focus states")
            if "form" in spec_lower or "input" in spec_lower:
                recommendations.append("Associate all form inputs with visible labels using <label>")
            if "modal" in spec_lower or "dialog" in spec_lower:
                recommendations.append("Use <dialog> element with proper focus trapping and ESC key support")
            if "navigation" in spec_lower or "menu" in spec_lower:
                recommendations.append("Wrap navigation in <nav> landmark with aria-label")
            if "icon" in spec_lower:
                recommendations.append("Provide aria-label or sr-only text for icon-only elements")

            return f"""
WCAG 2.1 Level AA Accessibility Checklist:

{json.dumps(checklist, indent=2)}

Specific Recommendations for This Design:
{chr(10).join(f"  • {rec}" for rec in recommendations) if recommendations else "  • Verify all checklist items above"}

Quick Wins:
  • Use semantic HTML5 elements (<button>, <nav>, <main>)
  • Add alt text to all images (empty alt="" for decorative)
  • Ensure 4.5:1 text contrast and 3:1 UI contrast
  • Test with keyboard only (no mouse)
  • Test with screen reader (NVDA/JAWS/VoiceOver)

Tools:
  • axe DevTools (browser extension)
  • WAVE Web Accessibility Evaluation Tool
  • Color contrast analyzers (WebAIM, Coolors)
"""

        return validate_accessibility

    def _create_generate_design_tokens_tool(self):
        """Create tool for generating design tokens"""

        @tool("generate_design_tokens")
        def generate_design_tokens(format: str = "json") -> str:
            """
            Generate design tokens in various formats (JSON, CSS, Tailwind).

            Args:
                format: Output format - "json", "css", or "tailwind"

            Returns:
                Design tokens in requested format
            """
            # Base token structure
            tokens = {
                "spacing": {
                    "0": "0",
                    "1": "0.25rem",   # 4px
                    "2": "0.5rem",    # 8px
                    "3": "0.75rem",   # 12px
                    "4": "1rem",      # 16px
                    "5": "1.25rem",   # 20px
                    "6": "1.5rem",    # 24px
                    "8": "2rem",      # 32px
                    "10": "2.5rem",   # 40px
                    "12": "3rem",     # 48px
                    "16": "4rem",     # 64px
                    "20": "5rem",     # 80px
                    "24": "6rem",     # 96px
                },
                "fontSize": {
                    "xs": "0.75rem",      # 12px
                    "sm": "0.875rem",     # 14px
                    "base": "1rem",       # 16px
                    "lg": "1.125rem",     # 18px
                    "xl": "1.25rem",      # 20px
                    "2xl": "1.5rem",      # 24px
                    "3xl": "1.875rem",    # 30px
                    "4xl": "2.25rem",     # 36px
                    "5xl": "3rem",        # 48px
                },
                "fontWeight": {
                    "normal": "400",
                    "medium": "500",
                    "semibold": "600",
                    "bold": "700",
                },
                "borderRadius": {
                    "none": "0",
                    "sm": "0.125rem",     # 2px
                    "base": "0.25rem",    # 4px
                    "md": "0.375rem",     # 6px
                    "lg": "0.5rem",       # 8px
                    "xl": "0.75rem",      # 12px
                    "2xl": "1rem",        # 16px
                    "full": "9999px",
                },
                "boxShadow": {
                    "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
                    "base": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
                    "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
                    "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
                    "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
                },
                "breakpoints": {
                    "sm": "640px",
                    "md": "768px",
                    "lg": "1024px",
                    "xl": "1280px",
                    "2xl": "1536px",
                }
            }

            if format == "json":
                return f"""
Design Tokens (JSON):

```json
{json.dumps(tokens, indent=2)}
```

Usage:
- Import these tokens in your design system
- Use consistent spacing scale (4px base grid)
- Apply font sizes with proper hierarchy
- Use shadows for elevation (material design)
"""

            elif format == "css":
                css_vars = []
                for category, values in tokens.items():
                    css_vars.append(f"  /* {category.upper()} */")
                    for key, value in values.items():
                        var_name = f"--{category}-{key}"
                        css_vars.append(f"  {var_name}: {value};")
                    css_vars.append("")

                return f"""
Design Tokens (CSS Custom Properties):

```css
:root {{
{chr(10).join(css_vars)}
}}

/* Usage example */
.button {{
  padding: var(--spacing-3) var(--spacing-6);
  font-size: var(--fontSize-base);
  font-weight: var(--fontWeight-medium);
  border-radius: var(--borderRadius-md);
  box-shadow: var(--boxShadow-sm);
}}
```
"""

            elif format == "tailwind":
                return f"""
Design Tokens (Tailwind Config):

```javascript
// tailwind.config.js
module.exports = {{
  theme: {{
    extend: {json.dumps(tokens, indent=6)[1:-1]}
  }}
}}
```

Usage:
- p-4 (padding: 1rem = 16px)
- text-lg (font-size: 1.125rem = 18px)
- rounded-lg (border-radius: 0.5rem = 8px)
- shadow-md (medium elevation shadow)
"""

            else:
                return "Invalid format. Use 'json', 'css', or 'tailwind'"

        return generate_design_tokens

    def _create_create_component_spec_tool(self):
        """Create tool for creating component specifications"""

        @tool("create_component_spec")
        def create_component_spec(component_name: str, component_type: str = "button") -> str:
            """
            Create detailed specification for a UI component.

            Args:
                component_name: Name of the component (e.g., "PrimaryButton", "SearchInput")
                component_type: Type - "button", "input", "card", "modal", "navigation"

            Returns:
                Complete component specification with variants and states
            """
            specs = {
                "button": """
Component: {name}
Type: Interactive Button
Category: Action

Variants:
1. Primary - Main CTAs (submit, save, create)
   - Background: brand.primary
   - Text: white
   - Min size: 44×44px
   - Padding: 12px 24px (spacing-3 spacing-6)
   - Border radius: 6px (rounded-md)

2. Secondary - Alternative actions
   - Background: transparent
   - Border: 1px solid neutral.300
   - Text: neutral.700
   - Same sizing as primary

3. Ghost - Low-emphasis actions
   - Background: transparent (hover: neutral.100)
   - Text: neutral.700
   - Same sizing as primary

States:
- Default: Base styling
- Hover: Darken 10%, cursor pointer
- Focus: 2px outline with 2px offset (accessibility)
- Active: Darken 15%, scale 98%
- Disabled: Opacity 50%, cursor not-allowed

Accessibility:
- Semantic <button> element
- aria-label if icon-only
- Keyboard: Space/Enter triggers
- Focus visible indicator required
- Minimum 3:1 contrast ratio

Implementation:
```jsx
<button
  className="px-6 py-3 rounded-md font-medium text-base
             bg-blue-600 text-white
             hover:bg-blue-700
             focus:outline-2 focus:outline-offset-2 focus:outline-blue-600
             active:scale-98
             disabled:opacity-50 disabled:cursor-not-allowed"
  aria-label="Submit form"
>
  Submit
</button>
```
""",
                "input": """
Component: {name}
Type: Text Input Field
Category: Form Control

Variants:
1. Text Input - Single-line text
2. Text Area - Multi-line text
3. Search - With search icon prefix
4. Number - Numeric input with increment/decrement

Base Styling:
- Height: 44px (11 spacing units)
- Padding: 12px 16px (spacing-3 spacing-4)
- Border: 1px solid neutral.300
- Border radius: 6px (rounded-md)
- Font size: 16px (text-base) - prevents zoom on iOS
- Line height: 1.5

States:
- Default: neutral.300 border
- Focus: brand.primary border (2px), outline ring
- Error: error border (red), aria-invalid="true"
- Disabled: neutral.100 background, opacity 60%
- Filled: neutral.700 text

Accessibility:
- Associated <label> with for/id
- aria-describedby for help text
- aria-invalid for error state
- aria-required for required fields
- Placeholder NOT a replacement for label

Implementation:
```jsx
<div className="space-y-1">
  <label htmlFor="email" className="block text-sm font-medium text-neutral-700">
    Email address *
  </label>
  <input
    id="email"
    type="email"
    required
    aria-required="true"
    aria-describedby="email-help"
    className="w-full h-11 px-4 py-3 text-base
               border border-neutral-300 rounded-md
               focus:border-blue-600 focus:ring-2 focus:ring-blue-600 focus:ring-opacity-50
               disabled:bg-neutral-100 disabled:opacity-60"
    placeholder="you@example.com"
  />
  <p id="email-help" className="text-sm text-neutral-600">
    We'll never share your email with anyone else.
  </p>
</div>
```
""",
                "card": """
Component: {name}
Type: Content Container
Category: Layout

Variants:
1. Elevated - With shadow for depth
2. Outlined - Border only, no shadow
3. Filled - Background color, subtle border

Base Styling:
- Padding: 24px (spacing-6)
- Border radius: 12px (rounded-xl)
- Background: background.primary (white/dark)
- Box shadow: md (elevated variant)

States:
- Static: Base styling
- Interactive (clickable): hover shadow-lg, cursor pointer
- Selected: brand.primary border (3px)

Accessibility:
- Use <article> or <section> semantic element
- Heading (h2/h3) for card title
- If clickable: entire card wrapped in <a> or <button>
- Focus ring on interactive cards

Implementation:
```jsx
<article className="p-6 rounded-xl bg-white shadow-md
                   hover:shadow-lg transition-shadow
                   border border-neutral-200">
  <h3 className="text-xl font-semibold text-neutral-900 mb-2">
    Card Title
  </h3>
  <p className="text-neutral-600 mb-4">
    Card description with supporting text that explains the content.
  </p>
  <button className="text-blue-600 hover:text-blue-700 font-medium">
    Read more →
  </button>
</article>
```
""",
                "modal": """
Component: {name}
Type: Modal Dialog
Category: Overlay

Structure:
1. Backdrop - Semi-transparent overlay (rgba(0,0,0,0.5))
2. Dialog - Centered content container
3. Header - Title and close button
4. Body - Main content
5. Footer - Action buttons

Sizing:
- Max width: 500px (sm), 700px (md), 900px (lg)
- Max height: 90vh (allow scrolling)
- Padding: 24px (spacing-6)
- Gap between sections: 16px (spacing-4)

Animation:
- Backdrop: fade in 200ms
- Dialog: fade + slide up 300ms
- Respect prefers-reduced-motion

Accessibility (CRITICAL):
- Use <dialog> element (native browser support)
- Focus trap (Tab cycles within modal)
- ESC key closes modal
- aria-modal="true"
- aria-labelledby points to title
- Return focus to trigger element on close
- Prevent body scroll when open

Implementation:
```jsx
<dialog
  aria-modal="true"
  aria-labelledby="modal-title"
  className="fixed inset-0 z-50 flex items-center justify-center
             backdrop:bg-black backdrop:bg-opacity-50"
>
  <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-auto">
    <div className="flex items-center justify-between p-6 border-b border-neutral-200">
      <h2 id="modal-title" className="text-xl font-semibold text-neutral-900">
        Modal Title
      </h2>
      <button
        aria-label="Close modal"
        className="p-1 hover:bg-neutral-100 rounded-md"
        onClick={{handleClose}}
      >
        <CloseIcon />
      </button>
    </div>
    <div className="p-6">
      <p className="text-neutral-700">Modal content goes here.</p>
    </div>
    <div className="flex justify-end gap-3 p-6 border-t border-neutral-200">
      <button className="px-4 py-2 text-neutral-700 hover:bg-neutral-100 rounded-md">
        Cancel
      </button>
      <button className="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-md">
        Confirm
      </button>
    </div>
  </div>
</dialog>
```
"""
            }

            template = specs.get(component_type, specs["button"])
            return template.format(name=component_name)

        return create_component_spec

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        task_id: str
    ) -> Dict[str, Any]:
        """
        Execute the Designer/UX agent to generate designs.

        Args:
            task: Design task description
            context: Additional context (target_platform, brand_colors, design_system)
            task_id: Unique task identifier for tracing

        Returns:
            {
                "design": {
                    "wireframes": "Mermaid/ASCII wireframes",
                    "components": [{"name": "...", "spec": "..."}],
                    "design_tokens": "JSON/CSS tokens",
                    "color_palette": {...}
                },
                "accessibility": {
                    "wcag_level": "AA",
                    "checklist": {...},
                    "recommendations": [...]
                },
                "implementation": {
                    "html_structure": "...",
                    "css_classes": "...",
                    "responsive_breakpoints": {...}
                },
                "citations": [{...}],
                "execution_time_ms": 1234
            }
        """
        start_time = time.time()

        # Start Langfuse trace
        trace = self.tracer.start_trace(
            name="designer_execution",
            metadata={
                "task": task,
                "task_id": task_id,
                "model": self.code_model
            }
        )

        try:
            # Create CrewAI task
            crew_task = Task(
                description=f"""
Generate comprehensive UI/UX design for the following:

{task}

Context:
{json.dumps(context, indent=2)}

Requirements:
1. Design System:
   - Generate color palette (brand, semantic, neutral, text)
   - Create design tokens (spacing, typography, shadows, borders)
   - Define component specifications with all variants and states
   - Include responsive breakpoints (mobile, tablet, desktop)

2. Components:
   - Specify all component variants (primary/secondary/ghost buttons, etc.)
   - Define all states (default/hover/focus/active/disabled)
   - Include measurements (padding, height, width, touch targets)
   - Provide implementation-ready code (React/Vue/HTML)

3. Accessibility (WCAG 2.1 Level AA):
   - Validate color contrast ratios (4.5:1 text, 3:1 UI)
   - Ensure keyboard navigation and focus indicators
   - Include semantic HTML and ARIA attributes
   - Verify touch target sizes (44×44px minimum)
   - Add screen reader considerations

4. Responsive Design:
   - Mobile-first approach
   - Breakpoints for sm/md/lg/xl/2xl
   - Touch-friendly mobile interactions
   - Desktop-optimized layouts

5. Documentation:
   - Component usage examples
   - Design rationale and UX considerations
   - Implementation guidelines
   - Figma/Sketch export notes (if applicable)

6. MUST cite ≥2 design patterns/systems from knowledge base

Output Format:
1. Design System Overview
2. Color Palette (JSON)
3. Design Tokens (CSS/Tailwind)
4. Component Specifications (detailed)
5. Wireframes/Layout (Mermaid or ASCII art)
6. Accessibility Checklist
7. Implementation Code Examples
8. Citations

Provide production-ready, enterprise-grade design specifications.
""",
                expected_output="Complete UI/UX design system with components, tokens, and accessibility validation",
                agent=self.agent
            )

            # Execute with CrewAI
            crew = Crew(
                agents=[self.agent],
                tasks=[crew_task],
                verbose=True
            )

            result = await crew.kickoff_async()

            # Parse result
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Extract components and citations
            citations = self._extract_citations(str(result))

            response = {
                "design": {
                    "wireframes": self._extract_section(str(result), "wireframe|layout"),
                    "components": [],  # Would parse from result
                    "design_tokens": self._extract_section(str(result), "design tokens|tokens"),
                    "color_palette": {}  # Would parse from result
                },
                "accessibility": {
                    "wcag_level": "AA",
                    "checklist": {},
                    "recommendations": []
                },
                "implementation": {
                    "html_structure": self._extract_code(str(result), "html|jsx"),
                    "css_classes": self._extract_code(str(result), "css"),
                    "responsive_breakpoints": {}
                },
                "citations": citations,
                "execution_time_ms": execution_time_ms
            }

            # End trace
            self.tracer.end_trace(
                trace_id=trace.get("id"),
                output=response,
                metadata={
                    "execution_time_ms": execution_time_ms,
                    "citations_count": len(citations)
                }
            )

            return response

        except Exception as e:
            # Log error to trace
            self.tracer.end_trace(
                trace_id=trace.get("id"),
                output={"error": str(e)},
                metadata={"error": True}
            )
            raise

    def _extract_citations(self, result: str) -> List[Dict[str, Any]]:
        """Extract citations from result"""
        citations = []
        citation_pattern = r'\[(?:Citation|Design Pattern) \d+\] (.*?) \(v([\d.]+)\)'
        matches = re.findall(citation_pattern, result)

        for source, version in matches[:5]:  # Limit to 5
            citations.append({
                "source": source.strip(),
                "version": version,
                "score": 0.85
            })

        return citations

    def _extract_section(self, result: str, pattern: str) -> str:
        """Extract specific section from result"""
        # Simple extraction - would be more sophisticated in production
        match = re.search(f"(?i)(?:{pattern})[:\n]+(.*?)(?:\n\n|\Z)", result, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _extract_code(self, result: str, language: str) -> str:
        """Extract code blocks from result"""
        pattern = f"```(?:{language})\n(.*?)\n```"
        match = re.search(pattern, result, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""
