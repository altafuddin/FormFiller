# backend/form_tools.py
'''
This module defines the schemas for our form-filling tools and the
handler functions that execute them, following the verified pattern.
'''

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.services.llm_service import FunctionCallParams

# Defines the schema for the open_form tool.
open_form_schema = FunctionSchema(
    name="open_form",
    description="Opens a new, empty form for the user to start filling out. Call this when the user says 'I want to fill a form' or similar.",
    properties={},
    required=[],
)

# Defines the schema for the update_field tool, including properties.
update_field_schema = FunctionSchema(
    name="update_field",
    description="Updates a specific field in the form with a new value provided by the user.",
    properties={
        "field_name": {
            "type": "string",
            "description": "The name of the form field to update (e.g. 'name', 'email').",
        },
        "field_value": {
            "type": "string",
            "description": "The value to place into the specified field (e.g. 'John Smith').",
        },
    },
    required=["field_name", "field_value"],
)

# Defines the schema for the submit_form tool.
submit_form_schema = FunctionSchema(
    name="submit_form",
    description="Submits the completed form. Call this when the user says 'Submit the form' or similar.",
    properties={},
    required=[]
)

# Creates a single ToolsSchema object containing all our defined function schemas.
tools = ToolsSchema(
    standard_tools=[
        open_form_schema,
        update_field_schema,
        submit_form_schema,
    ]
)

# --- Tool Handler Functions ---

async def handle_open_form(params: FunctionCallParams):
    """Handler for the open_form tool."""
    print(f"TOOL HANDLER: Executing open_form")
    # In a real app, this would trigger a message to the frontend.
    await params.result_callback({"status": "Form opened successfully."})

async def handle_update_field(params: FunctionCallParams):
    """Handler for the update_field tool."""
    field_name = params.arguments.get("field_name")
    field_value = params.arguments.get("field_value")
    print(f"TOOL HANDLER: Executing update_field with name='{field_name}' and value='{field_value}'")
    # In a real app, this would update a database and message the frontend.
    await params.result_callback({"status": f"Field '{field_name}' updated."})

async def handle_submit_form(params: FunctionCallParams):
    """Handler for the submit_form tool."""
    print(f"TOOL HANDLER: Executing submit_form")
    # In a real app, this would validate and submit the form data.
    await params.result_callback({"status": "Form submitted successfully."})