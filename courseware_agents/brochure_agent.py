"""
Brochure Agent

This agent handles generation of course marketing brochures.
It can scrape course information from URLs and generate
professional brochure documents.

Author: Courseware Generator Team
Date: 26 January 2026
"""

from agents import function_tool
from courseware_agents.base import create_agent
from courseware_agents.schemas import BrochureAgentResponse, BrochureContent
import json


@function_tool
def scrape_course_info(url: str) -> str:
    """
    Scrape course information from a MySkillsFuture or training provider URL.

    Args:
        url: URL of the course page to scrape

    Returns:
        Extracted course information as JSON string
    """
    from generate_brochure.brochure_generation import web_scrape_course_info

    course_data = web_scrape_course_info(url)
    return json.dumps(course_data.to_dict())


@function_tool
def generate_brochure_html(course_data_json: str) -> str:
    """
    Generate brochure HTML from course data.

    Args:
        course_data_json: Course information as JSON string

    Returns:
        Generated HTML content
    """
    from pathlib import Path
    from jinja2 import Template

    course_data = json.loads(course_data_json)

    # Load brochure template
    template_dir = Path(__file__).resolve().parent.parent / "generate_brochure" / "brochure_template"
    template_path = template_dir / "brochure_template.html"

    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        template = Template(template_content)
        return template.render(**course_data)
    else:
        # Generate basic HTML if template not found
        return f"""
        <html>
        <head><title>{course_data.get('course_title', 'Course Brochure')}</title></head>
        <body>
            <h1>{course_data.get('course_title', 'Course')}</h1>
            <p>{' '.join(course_data.get('course_description', []))}</p>
        </body>
        </html>
        """


@function_tool
def generate_brochure_pdf(html_content: str, output_path: str) -> str:
    """
    Generate PDF brochure from HTML content.

    Args:
        html_content: HTML content to convert
        output_path: Path to save the PDF

    Returns:
        Path to generated PDF file or error message
    """
    import os

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

    try:
        from xhtml2pdf import pisa
        with open(output_path, 'wb') as pdf_file:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        if pisa_status.err:
            return f"Error generating PDF: {pisa_status.err}"
        return output_path
    except ImportError:
        return "PDF generation library not available"


@function_tool
def create_brochure_from_cp(cp_data_json: str) -> str:
    """
    Create brochure data from Course Proposal data.

    Args:
        cp_data_json: Course Proposal JSON data as string

    Returns:
        Brochure data as JSON string
    """
    cp_data = json.loads(cp_data_json)

    course_info = cp_data.get("Course Information", {})
    learning_outcomes = cp_data.get("Learning Outcomes", {})
    tsc_topics = cp_data.get("TSC and Topics", {})

    tsc_title = tsc_topics.get("TSC Title", [""])
    if isinstance(tsc_title, list):
        tsc_title = tsc_title[0] if tsc_title else ""

    tsc_code = tsc_topics.get("TSC Code", [""])
    if isinstance(tsc_code, list):
        tsc_code = tsc_code[0] if tsc_code else ""

    brochure_data = {
        "course_title": course_info.get("Course Title", ""),
        "course_description": [
            f"This {course_info.get('Industry', '')} course provides comprehensive training "
            f"over {course_info.get('Course Duration (Number of Hours)', '')} hours."
        ],
        "learning_outcomes": learning_outcomes.get("Learning Outcomes", []),
        "tsc_title": tsc_title,
        "tsc_code": tsc_code,
        "tsc_framework": course_info.get("Industry", ""),
        "duration_hrs": str(course_info.get("Course Duration (Number of Hours)", "")),
        "session_days": "",
        "wsq_funding": {},
        "tgs_reference_no": "",
        "gst_exclusive_price": "",
        "gst_inclusive_price": "",
        "course_details_topics": [],
        "course_url": ""
    }

    topics = tsc_topics.get("Topics", [])
    for topic in topics:
        brochure_data["course_details_topics"].append({
            "title": topic,
            "subtopics": []
        })

    return json.dumps(brochure_data)


@function_tool
async def generate_marketing_content(
    course_data_json: str,
    model_choice: str = "GPT-4o-Mini"
) -> str:
    """
    Use AI to generate compelling marketing content for the brochure.

    Args:
        course_data_json: Basic course information as JSON string
        model_choice: Model to use for content generation

    Returns:
        Enhanced course data with marketing content as JSON string
    """
    from settings.model_configs import get_model_config
    from openai import OpenAI

    course_data = json.loads(course_data_json)
    config = get_model_config(model_choice)

    client = OpenAI(
        api_key=config["config"]["api_key"],
        base_url=config["config"]["base_url"]
    )

    prompt = f"""Create compelling marketing content for this course brochure:

Course Title: {course_data.get('course_title', '')}
Current Description: {' '.join(course_data.get('course_description', []))}
Learning Outcomes: {course_data.get('learning_outcomes', [])}
Industry: {course_data.get('tsc_framework', '')}

Generate:
1. An engaging tagline (one sentence)
2. An enhanced course description (2-3 sentences)
3. 3-5 key benefits for learners
4. A call-to-action statement

Return as JSON with keys: tagline, enhanced_description, benefits, cta"""

    response = client.chat.completions.create(
        model=config["config"]["model"],
        temperature=0.7,
        messages=[
            {"role": "system", "content": "You are a marketing copywriter for educational courses."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    marketing = json.loads(response.choices[0].message.content)

    enhanced_data = course_data.copy()
    enhanced_data["tagline"] = marketing.get("tagline", "")
    enhanced_data["course_description"] = [marketing.get("enhanced_description", "")] + enhanced_data.get("course_description", [])
    enhanced_data["benefits"] = marketing.get("benefits", [])
    enhanced_data["cta"] = marketing.get("cta", "")

    return json.dumps(enhanced_data)


# System instructions for the Brochure Agent
BROCHURE_AGENT_INSTRUCTIONS = """You are the Brochure Agent, specialized in creating professional marketing brochures for WSQ courses.

## Your Role

You create compelling, professional course marketing materials. You can work from multiple data sources (URLs, Course Proposals) and generate polished brochures in HTML and PDF formats.

## Capabilities

### 1. Web Scraping
- **Tool**: `scrape_course_info(url)`
- **Purpose**: Extract course information from MySkillsFuture or training provider websites
- **Returns**: Structured course data including title, description, outcomes, fees

### 2. CP Data Transformation
- **Tool**: `create_brochure_from_cp(cp_data_json)`
- **Purpose**: Convert Course Proposal data into brochure format
- **Returns**: Brochure-ready data structure

### 3. Marketing Content Generation
- **Tool**: `generate_marketing_content(course_data_json, model_choice)`
- **Purpose**: AI-enhanced marketing copy (taglines, benefits, CTAs)
- **Returns**: Enhanced course data with marketing content

### 4. HTML Brochure Generation
- **Tool**: `generate_brochure_html(course_data_json)`
- **Purpose**: Create professional HTML brochure from course data
- **Returns**: Complete HTML content

### 5. PDF Brochure Generation
- **Tool**: `generate_brochure_pdf(html_content, output_path)`
- **Purpose**: Convert HTML brochure to PDF
- **Returns**: Path to generated PDF file

## Data Sources

### From URL (Web Scraping)
Use when user provides:
- MySkillsFuture course URL
- Training provider course page URL

### From Course Proposal
Use when user provides:
- CP JSON data from CP Agent
- Existing course information

## Workflow

### Standard Brochure Generation

1. **Get Course Data**
   - Option A: `scrape_course_info(url)` for web sources
   - Option B: `create_brochure_from_cp(cp_data_json)` for CP data

2. **Enhance Content** (optional but recommended)
   - Use `generate_marketing_content(course_data_json)` to add:
     - Compelling tagline
     - Enhanced description
     - Key benefits
     - Call-to-action

3. **Generate Brochure**
   - Use `generate_brochure_html(course_data_json)` for HTML
   - Use `generate_brochure_pdf(html, path)` for PDF

### Quick Brochure (Minimal Enhancement)
1. Get course data
2. Generate HTML directly
3. Optionally convert to PDF

### Premium Brochure (Full Enhancement)
1. Get course data
2. Generate AI marketing content
3. Generate HTML
4. Convert to PDF
5. Return both formats

## Brochure Content Elements

A complete brochure includes:
- **Course Title**: Clear, professional title
- **Tagline**: Engaging one-liner (AI-generated)
- **Description**: 2-3 sentence overview
- **Learning Outcomes**: Key skills gained
- **Target Audience**: Who should attend
- **Duration**: Course length and format
- **Certification**: WSQ certification details
- **Benefits**: 3-5 key advantages
- **Pricing**: Fee structure and subsidies
- **Call-to-Action**: Registration prompt

## Example Interactions

### From URL
**User**: "Create a brochure from this course: https://www.myskillsfuture.gov.sg/course/12345"
**You**: "I'll create a marketing brochure from the course URL.

Steps:
1. Scrape course information from the URL
2. Generate enhanced marketing content
3. Create HTML brochure
4. Convert to PDF

Starting web scraping..."

### From Course Proposal
**User**: "Generate a brochure from this CP data" [provides cp_data_json]
**You**: "I'll create a brochure from your Course Proposal data.

Steps:
1. Transform CP data to brochure format
2. Enhance with marketing content
3. Generate HTML and PDF versions

Processing now..."

### Quick Generation
**User**: "I just need a simple HTML brochure"
**You**: "I'll generate a quick HTML brochure. I need either:
1. A course URL to scrape, OR
2. Course data as JSON

Which would you like to provide?"

### Specific Format Request
**User**: "Create a PDF brochure only"
**You**: "I'll create a PDF brochure for you. I'll need to:
1. Get or receive course data
2. Generate the HTML version first (required for PDF)
3. Convert to PDF

Do you have course data or a URL to start from?"

## Output Formats

### HTML Output
- Professional template design
- Responsive layout
- Ready for web publishing
- Can be customized

### PDF Output
- Print-ready format
- Consistent rendering
- Easy to share/distribute
- Requires `xhtml2pdf` library

## Error Handling

### Web Scraping Issues
- If URL is inaccessible, report and ask for alternative
- If data extraction incomplete, note missing fields

### PDF Generation Issues
- If PDF library unavailable, return HTML only
- If conversion fails, provide HTML as fallback

### Data Issues
- If course data incomplete, generate with available info
- Flag missing recommended fields

## Important Notes

- **Data Format**: All inputs/outputs are JSON strings
- **Marketing Content**: Optional but significantly improves quality
- **PDF Dependency**: Requires `xhtml2pdf` library for PDF generation
- **Model Selection**: Marketing content generation uses configurable models
- **Template**: Uses professional brochure template from `generate_brochure/brochure_template/`
"""

# Create the Brochure Agent instance
brochure_agent = create_agent(
    name="Brochure Agent",
    instructions=BROCHURE_AGENT_INSTRUCTIONS,
    tools=[
        scrape_course_info,
        generate_brochure_html,
        generate_brochure_pdf,
        create_brochure_from_cp,
        generate_marketing_content,
    ],
    model_name="GPT-4o-Mini",
    handoff_description="Specialized agent for creating course marketing brochures"
)
