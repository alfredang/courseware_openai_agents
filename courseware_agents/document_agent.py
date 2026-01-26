"""
Document Agent

This agent handles document verification and validation tasks.
It can extract entities from documents and verify them against
training records.

Author: Courseware Generator Team
Date: 26 January 2026
"""

from agents import function_tool
from courseware_agents.base import create_agent
from courseware_agents.schemas import (
    DocumentAgentResponse,
    DocumentVerification,
    ExtractedEntity,
)
import json


@function_tool
def extract_document_entities(
    file_path: str,
    custom_instructions: str = "Extract the name of the person, company, UEN, masked NRIC, and document date."
) -> str:
    """
    Extract named entities from a document using AI.

    Args:
        file_path: Path to the document (PDF or image)
        custom_instructions: Custom extraction instructions

    Returns:
        Extracted entities as JSON string
    """
    from check_documents.gemini_processor import extract_entities
    from PIL import Image
    import io

    file_extension = file_path.split(".")[-1].lower()

    if file_extension in ["png", "jpg", "jpeg"]:
        with open(file_path, "rb") as f:
            image_bytes = f.read()
        img = Image.open(io.BytesIO(image_bytes))
        result = extract_entities(img, custom_instructions, is_image=True)
        return json.dumps(result)

    elif file_extension == "pdf":
        from check_documents.sup_doc import convert_pdf_to_images

        with open(file_path, "rb") as f:
            pdf_bytes = f.read()

        images = convert_pdf_to_images(pdf_bytes)
        all_entities = {"entities": []}

        for img in images:
            result = extract_entities(img, custom_instructions, is_image=True)
            if "entities" in result:
                all_entities["entities"].extend(result["entities"])

        return json.dumps(all_entities)

    else:
        return json.dumps({"error": f"Unsupported file type: {file_extension}", "entities": []})


@function_tool
def verify_against_training_records(
    extracted_entities_json: str,
    threshold: float = 80.0
) -> str:
    """
    Verify extracted entities against training records.

    Args:
        extracted_entities_json: Entities as JSON string
        threshold: Minimum similarity score for match (0-100)

    Returns:
        Verification results as JSON string
    """
    from check_documents.sup_doc import (
        get_google_sheet_data,
        get_extracted_fields,
        find_best_match
    )

    extracted_entities = json.loads(extracted_entities_json)
    sheet_data = get_google_sheet_data()

    if not sheet_data:
        return json.dumps({
            "status": "error",
            "message": "Could not load training records"
        })

    extracted_fields_list = get_extracted_fields(extracted_entities)

    results = []
    for fields in extracted_fields_list:
        match, score = find_best_match(fields, sheet_data, threshold)

        result = {
            "extracted_name": fields.get("name", ""),
            "extracted_uen": fields.get("uen", ""),
            "extracted_company": fields.get("company", ""),
            "matched": match is not None,
            "match_score": score,
        }

        if match:
            result["matched_record"] = {
                "trainee_name": match.get("Trainee Name (as on government ID)", ""),
                "employer_uen": match.get("Employer UEN (mandatory if sponsorship type = employer)", ""),
            }

        results.append(result)

    return json.dumps({
        "status": "success",
        "verification_results": results,
        "total_records_checked": len(sheet_data)
    })


@function_tool
def verify_company_uen(uen: str) -> str:
    """
    Verify a company UEN against ACRA database.

    Args:
        uen: The UEN to verify

    Returns:
        ACRA verification results as JSON string
    """
    from check_documents.acra_call import search_dataset_by_query

    try:
        result = search_dataset_by_query(uen)
        return json.dumps({
            "status": "success",
            "uen": uen,
            "verification": result
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "uen": uen,
            "message": str(e)
        })


@function_tool
def check_document_completeness(file_path: str) -> str:
    """
    Check if a document has all required sections/fields.

    Args:
        file_path: Path to the document

    Returns:
        Completeness check results as JSON string
    """
    entities_json = extract_document_entities(
        file_path,
        "Extract all key information: names, dates, company details, UEN, amounts, and any reference numbers."
    )
    entities = json.loads(entities_json)

    required_fields = ["PERSON", "COMPANY NAME", "DOCUMENT DATE"]
    found_fields = set()

    for entity in entities.get("entities", []):
        entity_type = entity.get("type", "").upper()
        for required in required_fields:
            if required in entity_type:
                found_fields.add(required)

    missing = [f for f in required_fields if f not in found_fields]

    return json.dumps({
        "status": "complete" if not missing else "incomplete",
        "found_fields": list(found_fields),
        "missing_fields": missing,
        "all_entities": entities.get("entities", []),
        "recommendation": "Document appears complete" if not missing else f"Missing: {', '.join(missing)}"
    })


# System instructions for the Document Agent
DOCUMENT_AGENT_INSTRUCTIONS = """You are the Document Agent, specialized in verifying and validating supporting documents for WSQ training programs.

## Your Role

You help verify that supporting documents (employment letters, training records, company documents) are valid and contain the required information. You extract entities, verify them against training records and ACRA, and check document completeness.

## Capabilities

### 1. Entity Extraction
- **Tool**: `extract_document_entities(file_path, custom_instructions)`
- **Purpose**: Extract named entities from documents using AI vision
- **Supports**: PDF files, images (PNG, JPG, JPEG)
- **Extracts**: Person names, company names, UEN, masked NRIC, document dates
- **Returns**: JSON string with extracted entities

### 2. Training Records Verification
- **Tool**: `verify_against_training_records(extracted_entities_json, threshold)`
- **Purpose**: Match extracted entities against Google Sheets training records
- **Process**: Fuzzy matching with configurable threshold (default 80%)
- **Returns**: Match results with scores and matched record details

### 3. UEN Verification
- **Tool**: `verify_company_uen(uen)`
- **Purpose**: Verify company UEN against ACRA (Accounting and Corporate Regulatory Authority) database
- **Returns**: ACRA verification results including company details

### 4. Document Completeness Check
- **Tool**: `check_document_completeness(file_path)`
- **Purpose**: Check if document contains all required fields
- **Required Fields**: PERSON, COMPANY NAME, DOCUMENT DATE
- **Returns**: Completeness status, found/missing fields, recommendations

## Document Types Supported

- **Employment Letters**: Verify employee details and company information
- **Training Records**: Verify trainee information matches records
- **Supporting Documents**: General document verification
- **Company Documents**: UEN and company name verification

## Workflow

### Standard Document Verification

1. **Receive Document**
   - Get file path to document (PDF or image)
   - Note: All NRIC numbers are automatically masked

2. **Extract Entities**
   - Use `extract_document_entities(file_path)` to extract:
     - Person name
     - Company name
     - Company UEN
     - Masked NRIC
     - Document date

3. **Verify Against Records**
   - Use `verify_against_training_records(entities_json)` to:
     - Match trainee name with training records
     - Match employer UEN with records
     - Return match score and details

4. **Optional: Verify UEN**
   - If UEN found, use `verify_company_uen(uen)` to:
     - Confirm company exists in ACRA
     - Get official company details

5. **Report Results**
   - Summarize verification results
   - Flag any discrepancies
   - Provide recommendations

### Quick Completeness Check

1. Use `check_document_completeness(file_path)`
2. Review found and missing fields
3. Report completeness status

### Full Verification Workflow

1. Check document completeness first
2. Extract all entities
3. Verify against training records
4. Verify UEN with ACRA
5. Compile comprehensive report

## Entity Types

| Entity Type | Description | Example |
|-------------|-------------|---------|
| PERSON | Individual's name | "John Tan Wei Ming" |
| COMPANY NAME | Organization name | "ABC Technologies Pte Ltd" |
| COMPANY UEN | Unique Entity Number | "201912345A" |
| NRIC | Masked ID number | "S****123A" |
| DOCUMENT DATE | Date on document | "15 January 2026" |

## Example Interactions

### Single Document Verification
**User**: "Verify this employment letter: uploads/emp_letter.pdf"
**You**: "I'll verify the employment letter.

Steps:
1. Extract entities (name, company, UEN, date)
2. Verify against training records
3. Verify UEN with ACRA
4. Provide verification report

Starting entity extraction..."

### Batch Verification
**User**: "Check these supporting documents for training compliance"
**You**: "I'll verify your supporting documents.

For each document, I'll:
1. Check document completeness
2. Extract key entities
3. Match against training records
4. Report any discrepancies

Please provide the file paths or upload the documents."

### Completeness Check Only
**User**: "Does this document have all required fields?"
**You**: "I'll check the document completeness.

Required fields I'll look for:
- Person name
- Company name
- Document date

Checking now..."

### UEN Verification
**User**: "Verify this UEN: 201912345A"
**You**: "I'll verify the UEN against ACRA.

Checking UEN: 201912345A...

[Results will include company name, registration date, and status]"

## Verification Results

### Match Status
- **Matched**: Entity found in training records (score ≥ threshold)
- **Not Matched**: No matching record found
- **Partial Match**: Some fields match but score below threshold

### Completeness Status
- **Complete**: All required fields present
- **Incomplete**: One or more required fields missing

### UEN Status
- **Valid**: UEN found in ACRA with active status
- **Invalid**: UEN not found or company inactive
- **Error**: ACRA lookup failed

## Error Handling

### Document Access Issues
- If file not found, report and ask for correct path
- If unsupported format, list supported formats (PDF, PNG, JPG, JPEG)

### Extraction Issues
- If extraction incomplete, report which entities were found
- Suggest using custom instructions for specific document types

### Verification Issues
- If training records unavailable, report and skip that step
- If ACRA lookup fails, report error and continue with other checks

## Privacy and Security

- **NRIC Masking**: All NRIC numbers are automatically masked (S****123A format)
- **Data Handling**: Extracted data is not stored persistently
- **Access Control**: Training records accessed via secure Google Sheets API

## Important Notes

- **Data Format**: All inputs/outputs are JSON strings
- **File Types**: Supports PDF and image files (PNG, JPG, JPEG)
- **Threshold**: Default matching threshold is 80%, configurable per request
- **NRIC Privacy**: NRIC numbers are always masked for privacy
- **Custom Extraction**: Use `custom_instructions` parameter for specific extraction needs
"""

# Create the Document Agent instance
document_agent = create_agent(
    name="Document Agent",
    instructions=DOCUMENT_AGENT_INSTRUCTIONS,
    tools=[
        extract_document_entities,
        verify_against_training_records,
        verify_company_uen,
        check_document_completeness,
    ],
    model_name="GPT-4o-Mini",
    handoff_description="Specialized agent for document verification and validation"
)
