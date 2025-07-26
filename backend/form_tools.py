# backend/form_tools.py
'''
This module defines the schemas for our form-filling tools and the
handler functions that execute them. Handlers now also push UI update
messages to the client via the RTVIProcessor.
'''
import asyncio
import time
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.services.llm_service import FunctionCallParams
from pipecat.processors.frameworks.rtvi import RTVIProcessor

# Performance tracking
class PerformanceTracker:
    def __init__(self):
        self.start_time = None
    
    def start(self):
        self.start_time = time.time()
    
    def end(self, operation):
        if self.start_time:
            duration = (time.time() - self.start_time) * 1000  # Convert to ms
            print(f"⚡ {operation} completed in {duration:.1f}ms")
            return duration
        return 0
    
# Global performance tracker
perf_tracker = PerformanceTracker()


# --- Form Definitions ---
# This dictionary is the "source of truth" for the structure of all forms.
# This allows for easy extension with new form types in the future.
FORM_DEFINITIONS = {
    "registration": [
        {"name": "name", "label": "Full Name", "type": "text"},
        {"name": "email", "label": "Email Address", "type": "email"},
        # {"name": "phone_number", "label": "Phone Number", "type": "tel"},
    ]
}

# --- Tool Schema Definitions ---
# Defines the schema for the open_form tool.
open_form_schema = FunctionSchema(
    name="open_form",
    description="Opens form instantly. Should be called when a user wants to start a new form.",
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
    description="Submits form instantly. Call this when the user says 'Submit the form' or similar.",
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

# --- Ultra-Fast Tool Handlers ---

async def handle_open_form(rtvi: RTVIProcessor, params: FunctionCallParams):
    """Ultra-fast form opening handler"""
    perf_tracker.start()
    
    form_type = params.arguments.get("form_type", "registration")
    print(f"🚀 SPEED: Opening {form_type} form...")
    
    # Minimal form definition for speed
    form_definition = [
        {"name": "name", "label": "Name", "type": "text"},
        {"name": "email", "label": "Email", "type": "email"}, 
        # {"name": "phone_number", "label": "Phone", "type": "tel"},
    ]
    
    # Fire UI update and callback simultaneously 
    ui_task = rtvi.send_server_message({
        "type": "open_form",
        "payload": {"form_type": form_type, "fields": form_definition},
    })
    
    callback_task = params.result_callback({"status": "READY"})
    
    # Execute both in parallel for maximum speed
    await asyncio.gather(ui_task, callback_task)
    
    perf_tracker.end("open_form")

async def handle_update_field(rtvi: RTVIProcessor, params: FunctionCallParams):
    """Ultra-fast field update handler"""
    perf_tracker.start()
    
    field_name = params.arguments.get("field_name")
    field_value = params.arguments.get("field_value")
    print(f"⚡ SPEED: Updating {field_name}={field_value}")
    
    # Parallel UI update and callback
    ui_task = rtvi.send_server_message({
        "type": "update_field",
        "payload": {"field_name": field_name, "field_value": field_value},
    })
    
    callback_task = params.result_callback({"status": "UPDATED"})
    
    await asyncio.gather(ui_task, callback_task)
    
    perf_tracker.end(f"update_field_{field_name}")

async def handle_submit_form(rtvi: RTVIProcessor, params: FunctionCallParams):
    """Ultra-fast form submission handler"""
    perf_tracker.start()
    print(f"🏁 SPEED: Submitting form...")
    
    # Parallel submission and callback
    ui_task = rtvi.send_server_message({
        "type": "submit_form", 
        "payload": {"status": "success"},
    })
    
    callback_task = params.result_callback({"status": "SUBMITTED"})
    
    await asyncio.gather(ui_task, callback_task)
    
    perf_tracker.end("submit_form")