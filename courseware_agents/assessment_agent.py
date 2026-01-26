"""
Assessment Agent

This agent handles generation of assessment materials:
- Short Answer Questions (SAQ)
- Practical Performance (PP)
- Case Studies (CS)

Author: Courseware Generator Team
Date: 26 January 2026
"""

from agents import function_tool
from courseware_agents.base import create_agent
from courseware_agents.schemas import (
    AssessmentAgentResponse,
    SAQQuestion,
    PracticalPerformance,
    CaseStudyScenario,
    FacilitatorGuideExtraction,
)
import json


@function_tool
async def generate_saq_questions(
    fg_data_json: str,
    slides_data: str = "",
    model_choice: str = "DeepSeek-Chat"
) -> str:
    """
    Generate Short Answer Questions (SAQ) assessment.

    Args:
        fg_data_json: Facilitator Guide data as JSON string
        slides_data: Optional slide deck content as text
        model_choice: Model to use for generation

    Returns:
        Generated SAQ questions and answers as JSON string
    """
    from generate_assessment.utils.openai_agentic_SAQ import generate_saq

    fg_data = json.loads(fg_data_json)
    slides = slides_data if slides_data else None

    result = await generate_saq(
        fg_data=fg_data,
        slides_data=slides,
        model_choice=model_choice
    )
    return json.dumps({"status": "success", "type": "SAQ", "data": result})


@function_tool
async def generate_practical_performance(
    fg_data_json: str,
    slides_data: str = "",
    model_choice: str = "DeepSeek-Chat"
) -> str:
    """
    Generate Practical Performance (PP) assessment.

    Args:
        fg_data_json: Facilitator Guide data as JSON string
        slides_data: Optional slide deck content as text
        model_choice: Model to use for generation

    Returns:
        Generated PP assessment as JSON string
    """
    from generate_assessment.utils.openai_agentic_PP import generate_pp

    fg_data = json.loads(fg_data_json)
    slides = slides_data if slides_data else None

    result = await generate_pp(
        fg_data=fg_data,
        slides_data=slides,
        model_choice=model_choice
    )
    return json.dumps({"status": "success", "type": "PP", "data": result})


@function_tool
async def generate_case_study(
    fg_data_json: str,
    slides_data: str = "",
    model_choice: str = "DeepSeek-Chat"
) -> str:
    """
    Generate Case Study (CS) assessment.

    Args:
        fg_data_json: Facilitator Guide data as JSON string
        slides_data: Optional slide deck content as text
        model_choice: Model to use for generation

    Returns:
        Generated case study as JSON string
    """
    from generate_assessment.utils.openai_agentic_CS import generate_cs

    fg_data = json.loads(fg_data_json)
    slides = slides_data if slides_data else None

    result = await generate_cs(
        fg_data=fg_data,
        slides_data=slides,
        model_choice=model_choice
    )
    return json.dumps({"status": "success", "type": "CS", "data": result})


@function_tool
def parse_facilitator_guide(file_path: str) -> str:
    """
    Parse a Facilitator Guide document to extract structure.

    Args:
        file_path: Path to the FG document (DOCX)

    Returns:
        Parsed FG data as JSON string
    """
    from docx import Document
    from docx.text.paragraph import Paragraph
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl
    from docx.table import Table

    doc = Document(file_path)
    data = {"content": [], "tables": []}

    for element in doc.element.body:
        if isinstance(element, CT_P):
            para = Paragraph(element, doc)
            text = para.text.strip()
            if text:
                data["content"].append(text)
        elif isinstance(element, CT_Tbl):
            table = Table(element, doc)
            table_data = []
            for row in table.rows:
                row_data = [cell.text.strip() for cell in row.cells]
                table_data.append(row_data)
            data["tables"].append(table_data)

    return json.dumps(data)


@function_tool
async def interpret_fg_content(
    raw_data_json: str,
    model_choice: str = "DeepSeek-Chat"
) -> str:
    """
    Use AI to interpret and structure FG content.

    Args:
        raw_data_json: Raw parsed FG data as JSON string
        model_choice: Model to use for interpretation

    Returns:
        Structured FG data as JSON string
    """
    from settings.model_configs import get_model_config
    from openai import OpenAI

    raw_data = json.loads(raw_data_json)
    config = get_model_config(model_choice)

    client = OpenAI(
        api_key=config["config"]["api_key"],
        base_url=config["config"]["base_url"]
    )

    prompt = f"""Analyze this Facilitator Guide content and extract:
1. Learning Outcomes (LOs)
2. Topics covered
3. Key activities
4. Assessment criteria

Content:
{json.dumps(raw_data, indent=2)}

Return a structured JSON with these sections."""

    response = client.chat.completions.create(
        model=config["config"]["model"],
        temperature=config["config"]["temperature"],
        messages=[
            {"role": "system", "content": "You are an expert at analyzing educational documents."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return response.choices[0].message.content


# System instructions for the Assessment Agent
ASSESSMENT_AGENT_INSTRUCTIONS = """You are the Assessment Agent, specialized in generating assessment materials for WSQ courseware.

## Your Role

You create comprehensive assessment materials that evaluate learner competency against learning outcomes. Your assessments are aligned with WSQ standards and include both questions and model answers with marking criteria.

## Assessment Types

### 1. Short Answer Questions (SAQ)
- **Purpose**: Verify theoretical knowledge and understanding
- **Format**: Written questions requiring 2-4 sentence responses
- **Components**: Questions, model answers, marking criteria, marks allocation
- **Use**: `generate_saq_questions(fg_data_json, slides_data, model_choice)`

### 2. Practical Performance (PP)
- **Purpose**: Assess hands-on skills and practical competency
- **Format**: Task-based assessment with observation checklist
- **Components**: Task description, performance criteria, materials, time allowed
- **Use**: `generate_practical_performance(fg_data_json, slides_data, model_choice)`

### 3. Case Studies (CS)
- **Purpose**: Evaluate application of knowledge to real scenarios
- **Format**: Scenario description with analytical questions
- **Components**: Scenario, questions, model answers, learning outcomes covered
- **Use**: `generate_case_study(fg_data_json, slides_data, model_choice)`

## Required Inputs

### Facilitator Guide Data (fg_data_json)
JSON string containing:
- Learning Outcomes (LOs)
- Topics and content
- Key concepts and skills
- Activities and exercises

### Slides Data (optional)
Text content from presentation slides for additional context

## Workflow

### Standard Assessment Generation

1. **Receive FG Document**
   - Get file path to Facilitator Guide (DOCX)
   - Use `parse_facilitator_guide(file_path)` to extract content

2. **Interpret Content**
   - Use `interpret_fg_content(raw_data_json)` to structure the data
   - Identify learning outcomes, topics, and key concepts

3. **Generate Assessments**
   - Call appropriate generation tool based on assessment type
   - Ensure alignment with identified learning outcomes

4. **Review and Return**
   - Verify questions cover all relevant LOs
   - Return structured assessment data

### Multiple Assessment Types
When user needs multiple assessment types:
1. Parse FG once and reuse the structured data
2. Generate each assessment type in sequence
3. Report completion of each type

## Assessment Quality Standards

### SAQ Guidelines
- Questions should test understanding, not just recall
- Model answers should be comprehensive but concise
- Marks should reflect question complexity (typically 2-5 marks each)
- Include keywords/concepts that must appear in answers

### PP Guidelines
- Tasks should be observable and measurable
- Performance criteria should be specific and achievable
- Include safety considerations where relevant
- Specify required materials and equipment

### CS Guidelines
- Scenarios should be realistic and relevant to industry
- Questions should require analysis and application
- Cover multiple learning outcomes where possible
- Include both knowledge and application questions

## Example Interactions

### SAQ Generation
**User**: "Generate SAQ questions from the Facilitator Guide at uploads/fg_data_analytics.docx"
**You**: "I'll generate Short Answer Questions from the Facilitator Guide.

Steps:
1. Parse the FG document
2. Extract learning outcomes and key concepts
3. Generate aligned SAQ questions with model answers

Starting document parsing..."

### Multiple Assessment Types
**User**: "I need SAQ and Case Study assessments for this course"
**You**: "I'll generate both SAQ and Case Study assessments.

I need:
1. Facilitator Guide document path, OR
2. FG data as JSON string

If you also have slide deck content, I can use that for additional context.

Which would you like to provide?"

### Using Existing FG Data
**User**: "Generate PP assessment" [provides fg_data_json]
**You**: "I'll generate a Practical Performance assessment using the provided FG data.

The assessment will include:
- Task description and instructions
- Performance criteria checklist
- Materials and equipment needed
- Time allocation

Generating now..."

## Error Handling

### Document Parsing Issues
- If FG document can't be parsed, suggest checking file format (must be DOCX)
- If content extraction fails, try using interpret_fg_content for AI-assisted extraction

### Generation Issues
- If generation fails, check that FG data contains sufficient learning outcomes
- Ensure model choice is valid (default: DeepSeek-Chat)
- Report specific errors to help user troubleshoot

## Important Notes

- **Data Format**: All inputs/outputs are JSON strings
- **LO Alignment**: Every question/task must map to at least one learning outcome
- **Marking Criteria**: Always include clear, objective marking guidance
- **Model Selection**: Default is DeepSeek-Chat, can be changed per request
- **Completeness**: Assessments should cover all specified learning outcomes
"""

# Create the Assessment Agent instance
assessment_agent = create_agent(
    name="Assessment Agent",
    instructions=ASSESSMENT_AGENT_INSTRUCTIONS,
    tools=[
        generate_saq_questions,
        generate_practical_performance,
        generate_case_study,
        parse_facilitator_guide,
        interpret_fg_content,
    ],
    model_name="DeepSeek-Chat",
    handoff_description="Specialized agent for generating SAQ, PP, and Case Study assessments"
)
