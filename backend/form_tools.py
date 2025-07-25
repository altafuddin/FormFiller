# backend/form_tools.py
'''
This module defines the schemas for our form-filling tools and the
handler functions that execute them. Handlers now also push UI update
messages to the client via the RTVIProcessor.
'''

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.services.llm_service import FunctionCallParams
from pipecat.processors.frameworks.rtvi import RTVIProcessor

# --- Form Definitions ---
# This dictionary is the "source of truth" for the structure of all forms.
# This allows for easy extension with new form types in the future.
FORM_DEFINITIONS = {
    "registration": [
        {"name": "name", "label": "Full Name", "type": "text"},
        {"name": "email", "label": "Email Address", "type": "email"},
        {"name": "phone_number", "label": "Phone Number", "type": "tel"},
    ]
}

# --- Tool Schema Definitions ---
# Defines the schema for the open_form tool.
open_form_schema = FunctionSchema(
    name="open_form",
    description="Opens a form of a specific type. Should be called when a user wants to start a new form.",
    properties={
        "form_type": {
            "type": "string",
            "description": "The type of form to open.",
            "enum": ["registration"],
        }
    },
    required=["form_type"],
)

# Defines the schema for the update_field tool, including properties.
update_field_schema = FunctionSchema(
    name="update_field",
    description="Updates a specific field in the form with a new value provided by the user. Call this immediately after the user provides information for a field.",
    properties={
        "field_name": {
            "type": "string",
            "description": "The name of the form field to update (e.g. 'name', 'email', 'phone number', etc.).",
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

async def handle_open_form(rtvi: RTVIProcessor, params: FunctionCallParams):
    """Handler for the open_form tool.

    This handler now performs two actions:
    1. It pushes an `RTVIServerMessageFrame` to the client to render the form UI.
    2. It calls `result_callback` to let the LLM know the tool executed successfully.
    """
    form_type = params.arguments.get("form_type", "unknown")
    print(f"TOOL HANDLER: Executing open_form for form_type: '{form_type}'")

    
    form_definition = FORM_DEFINITIONS.get(form_type, [])
    ui_message = {
            "type": "open_form",
            "payload": {
                "form_type": form_type,
                "fields": form_definition,
            },
        }

    # The frame is now pushed to the `rtvi` processor, which is the correct
    # component for handling UI-bound messages.
    await rtvi.send_server_message(ui_message)

    # Let the LLM know the tool call was successful.
    await params.result_callback({"status": f"Form '{form_type}' opened successfully."})

async def handle_update_field(rtvi: RTVIProcessor, params: FunctionCallParams):
    """
    Handler for the update_field tool.
    Sends a message to the client UI to update a specific field's value.
    """
    try:
        field_name = params.arguments.get("field_name")
        field_value = params.arguments.get("field_value")
        print(f"TOOL HANDLER: Executing update_field with name='{field_name}' and value='{field_value}'")

        # Create the UI message frame for updating a field.
        ui_message = {
                "type": "update_field",
                "payload": {
                    "field_name": field_name,
                    "field_value": field_value,
                },
            }

        # Push the frame to the client.
        await rtvi.send_server_message(ui_message)

        # Let the LLM know the tool call was successful.
        await params.result_callback({"status": f"Field '{field_name}' updated."})
        
    except Exception as e:
        await params.result_callback({"error": f"Failed to update field: {str(e)}"})

async def handle_submit_form(rtvi: RTVIProcessor, params: FunctionCallParams):
    """
    Handler for the submit_form tool.
    Sends a message to the client UI to signal completion and clear the form.
    """
    print(f"TOOL HANDLER: Executing submit_form")

    # Create the UI message frame for form submission.
    ui_message = {
            "type": "submit_form",
            "payload": {"status": "success"},
        }
    
    # Push the frame to the client.
    await rtvi.send_server_message(ui_message)

    # Let the LLM know the tool call was successful.
    await params.result_callback({"status": "Form submitted successfully."})