"""Pydantic models and prompts for UI schema generation"""

from pydantic import BaseModel, Field
from typing import list, Optional
from langchain_core.prompts import ChatPromptTemplate

# ============= PYDANTIC MODELS =============
class UIValidation(BaseModel):
    """Validation rules for form inputs"""
    errorMessage: Optional[str] = Field(None, description="Error message to display on validation faliure")

class UIElement(BaseModel):
    """A single UI component element"""
    id: str = Field(..., description="Unique identifier for the elememt")
    type: str = Field(..., description="input | checkbox | text | link | container")
    group: Optional[str] = Field(None, description="Section grouping (e.g. header, form, footer)")
    label: str = Field(..., description="Visible label context")
    inputType: Optional[str] = Field(None, description="text | email | password | number (for inputs only)")
    placeholder: Optional[str] = Field(None, description="Placeholder text")
    required: Optional[bool] = Field(False, description="Whether the field is required")
    ariaLabel: Optional[str] = Field(None, description="Accessible aria-label if different from label")
    helperText: Optional[str] = Field(None, description="Small helper or hint text below")
    validation: Optional[UIValidation] = Field(None, description="Validation rules for inputs")
    variant: Optional[str] = Field(None, description="primary | secondary (for buttons only)")
    icon: Optional[str] = Field(None, description="Optional heroicon name or SVG description (e.g. 'user', 'lock')")

class ScreenSchema(BaseModel):
    """Schema for a single screen/page"""
    screen_name: str = Field(..., description="Short descriptive titles")
    components: list[UIElement] = Field(..., description="List of UI components")

class UISchemaResponse(BaseModel):
    """Response model for UI schema generation"""
    ui_schema: ScreenSchema = Field(...,description="The generated UI Schema" )
    generated_by: str = Field(default="open-source LLM")
    model_used: str = Field(default="llama-3.3-70b")

# ============= PROMPTS =============

UI_SCHEMA_SYSTEM_PROMPT = """You are an expert senior UI/UX designer and Tailwind CSS specialist in 2026. Your task is to generate a **high-fidelity, modern, professional, responsive web UI schema** in strict JSON format for the given screen/task.

Rules you MUST follow strictly:
- Output ONLY valid JSON — no explanations, no code blocks, no markdown. Start directly with {{ and end with }}.
- Schema structure MUST match this exact format:
  {{
    "ui_schema": {{
      "screen_name": "Short descriptive title",
      "components": [
        {{
          "id": "unique-string-id",
          "type": "input | checkbox | button | text | link | container",
          "group": "optional-group-name (e.g. header, form, footer)",
          "label": "Visible label text",
          "inputType": "text | email | password | number (for inputs only)",
          "placeholder": "Placeholder text",
          "required": true/false,
          "ariaLabel": "Accessible aria-label if different from label",
          "helperText": "Small helper or hint text below",
          "validation": {{ "errorMessage": "Error text to show on invalid" }},
          "variant": "primary | secondary (for buttons only)",
          "icon": "optional-heroicon-name or SVG (e.g. 'user', 'lock')"
        }}
      ]
    }},
    "generated_by": "open-source LLM",
    "model_used": "llama-3.3-70b"
  }}

Design Standards for 2026:
- Modern aesthetic: neumorphic/soft shadows, subtle gradients, glassmorphism (backdrop-blur), micro-animations
- Responsive: mobile-first design, components stack on mobile
- Accessibility (WCAG 2.2 AA): semantic labels, aria-*, focus-visible rings, sufficient contrast, keyboard nav
- Visual richness: headings (text type with bold/large), icons on buttons/inputs, helper text, error states
- For login/authentication: eye icon for password toggle, remember me checkbox, forgot password link, branded header
- Logical grouping via "group" field to create visual sections
- Keep schema concise: 8-15 components max per screen

{format_instructions}"""

UI_SCHEMA_HUMAN_PROMPT = """Inputs for this generation:
- Requirements: {requirements}
- Use cases: {use_cases}
- Screen: {screen}
- NFRs: {nfrs}
- Context: {context}

Generate the improved JSON schema now."""

def get_ui_schema_prompt() -> ChatPromptTemplate:
    """Pydantic models and prompts for UI schema generation"""

from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate

# ============= PYDANTIC MODELS =============

class UIValidation(BaseModel):
    """Validation rules for form inputs"""
    errorMessage: Optional[str] = Field(None, description="Error message to display on validation failure")


class UIElement(BaseModel):
    """A single UI component element"""
    id: str = Field(..., description="Unique identifier for the element")
    type: str = Field(..., description="input | checkbox | button | text | link | container")
    group: Optional[str] = Field(None, description="Section grouping (e.g. header, form, footer)")
    label: str = Field(..., description="Visible label text")
    inputType: Optional[str] = Field(None, description="text | email | password | number (for inputs only)")
    placeholder: Optional[str] = Field(None, description="Placeholder text")
    required: Optional[bool] = Field(False, description="Whether the field is required")
    ariaLabel: Optional[str] = Field(None, description="Accessible aria-label if different from label")
    helperText: Optional[str] = Field(None, description="Small helper or hint text below")
    validation: Optional[UIValidation] = Field(None, description="Validation rules for inputs")
    variant: Optional[str] = Field(None, description="primary | secondary (for buttons only)")
    icon: Optional[str] = Field(None, description="Optional heroicon name or SVG description (e.g. 'user', 'lock')")


class ScreenSchema(BaseModel):
    """Schema for a single screen/page"""
    screen_name: str = Field(..., description="Short descriptive title")
    components: List[UIElement] = Field(..., description="List of UI components")


class UISchemaResponse(BaseModel):
    """Response model for UI schema generation"""
    ui_schema: ScreenSchema = Field(..., description="The generated UI schema")
    generated_by: str = Field(default="open-source LLM")
    model_used: str = Field(default="llama-3.3-70b")


# ============= PROMPTS =============

UI_SCHEMA_SYSTEM_PROMPT = """You are an expert senior UI/UX designer and Tailwind CSS specialist in 2026. Your task is to generate a **high-fidelity, modern, professional, responsive web UI schema** in strict JSON format for the given screen/task.

Rules you MUST follow strictly:
- Output ONLY valid JSON — no explanations, no code blocks, no markdown. Start directly with {{ and end with }}.
- Schema structure MUST match this exact format:
  {{
    "ui_schema": {{
      "screen_name": "Short descriptive title",
      "components": [
        {{
          "id": "unique-string-id",
          "type": "input | checkbox | button | text | link | container",
          "group": "optional-group-name (e.g. header, form, footer)",
          "label": "Visible label text",
          "inputType": "text | email | password | number (for inputs only)",
          "placeholder": "Placeholder text",
          "required": true/false,
          "ariaLabel": "Accessible aria-label if different from label",
          "helperText": "Small helper or hint text below",
          "validation": {{ "errorMessage": "Error text to show on invalid" }},
          "variant": "primary | secondary (for buttons only)",
          "icon": "optional-heroicon-name or SVG (e.g. 'user', 'lock')"
        }}
      ]
    }},
    "generated_by": "open-source LLM",
    "model_used": "llama-3.3-70b"
  }}

Design Standards for 2026:
- Modern aesthetic: neumorphic/soft shadows, subtle gradients, glassmorphism (backdrop-blur), micro-animations
- Responsive: mobile-first design, components stack on mobile
- Accessibility (WCAG 2.2 AA): semantic labels, aria-*, focus-visible rings, sufficient contrast, keyboard nav
- Visual richness: headings (text type with bold/large), icons on buttons/inputs, helper text, error states
- For login/authentication: eye icon for password toggle, remember me checkbox, forgot password link, branded header
- Logical grouping via "group" field to create visual sections
- Keep schema concise: 8-15 components max per screen

{format_instructions}"""

UI_SCHEMA_HUMAN_PROMPT = """Inputs for this generation:
- Requirements: {requirements}
- Use cases: {use_cases}
- Screen: {screen}
- NFRs: {nfrs}
- Context: {context}

Generate the improved JSON schema now."""


def get_ui_schema_prompt() -> ChatPromptTemplate:
    """Returns the ChatPromptTemplate for UI schema generation"""
    return ChatPromptTemplate.from_messages([
        ("system", UI_SCHEMA_SYSTEM_PROMPT),
        ("human", UI_SCHEMA_HUMAN_PROMPT)
    ])

