# backend/form_tools.py
'''
This module defines the schemas for our form-filling tools and the
handler functions that execute them. Handlers now also push UI update
messages to the client via the RTVIProcessor.
'''
import asyncio
import time
from collections import defaultdict
from datetime import datetime
import statistics
import json

# Pipecat imports
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.services.llm_service import FunctionCallParams
from pipecat.processors.frameworks.rtvi import RTVIProcessor

# Performance tracking
class AdvancedPerformanceTracker:
    def __init__(self):
        self.metrics = defaultdict(list)
        self.voice_latency_data = []
        
    def start_voice_interaction(self):
        return time.time()
    
    def end_voice_interaction(self, start_time, interaction_type="general"):
        if start_time:
            latency_ms = (time.time() - start_time) * 1000
            self.voice_latency_data.append({
                'timestamp': datetime.now().isoformat(),
                'type': interaction_type,
                'latency_ms': latency_ms
            })
            print(f"🎙️ Voice-to-Voice {interaction_type}: {latency_ms:.1f}ms")
            return latency_ms
        return 0
    
    def track_tool_performance(self, tool_name, duration_ms):
        self.metrics[tool_name].append(duration_ms)
        print(f"⚡ {tool_name} completed in {duration_ms:.1f}ms")
    
    def get_performance_summary(self):
        summary = {}
        
        for tool_name, durations in self.metrics.items():
            if durations:
                summary[tool_name] = {
                    'count': len(durations),
                    'avg_ms': statistics.mean(durations),
                    'median_ms': statistics.median(durations),
                    'min_ms': min(durations),
                    'max_ms': max(durations),
                    'p95_ms': statistics.quantiles(durations, n=20)[18] if len(durations) > 5 else max(durations)
                }
        
        if self.voice_latency_data:
            latencies = [d['latency_ms'] for d in self.voice_latency_data]
            summary['voice_to_voice'] = {
                'count': len(latencies),
                'avg_ms': statistics.mean(latencies),
                'median_ms': statistics.median(latencies),
                'p95_ms': statistics.quantiles(latencies, n=20)[18] if len(latencies) > 5 else max(latencies),
                'under_500ms': sum(1 for l in latencies if l < 500) / len(latencies) * 100
            }
        
        return summary
    
    def export_data(self, filename="performance_data.json"):
        data = {
            'metrics': dict(self.metrics),
            'voice_latency': self.voice_latency_data,
            'export_time': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"📊 Data exported to {filename}")

# Global performance tracker instance
enhanced_perf_tracker = AdvancedPerformanceTracker()


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

# --- Tool Handlers ---

async def handle_open_form(rtvi: RTVIProcessor, params: FunctionCallParams):
    """"Handles the open_form tool call by sending a UI update message to the client
    and returning a result callback."""
    start_time = time.time()
    voice_start = enhanced_perf_tracker.start_voice_interaction()
    
    form_type = params.arguments.get("form_type", "registration")
    print(f"🚀 Opening {form_type} form...")
    
    form_definition = [
        {"name": "name", "label": "Name", "type": "text"},
        {"name": "email", "label": "Email", "type": "email"}, 
    ]
    
    ui_task = rtvi.send_server_message({
        "type": "open_form",
        "payload": {"form_type": form_type, "fields": form_definition},
    })
    
    callback_task = params.result_callback({"status": "READY"})
    
    await asyncio.gather(ui_task, callback_task)
    
    tool_duration = (time.time() - start_time) * 1000
    enhanced_perf_tracker.track_tool_performance("open_form", tool_duration)
    enhanced_perf_tracker.end_voice_interaction(voice_start, "form_opening")

async def handle_update_field(rtvi: RTVIProcessor, params: FunctionCallParams):
    """Handles the update_field tool call by sending a UI update message to the client
    and returning a result callback."""
    start_time = time.time()
    voice_start = enhanced_perf_tracker.start_voice_interaction()
    
    field_name = params.arguments.get("field_name")
    field_value = params.arguments.get("field_value")
    
    ui_task = rtvi.send_server_message({
        "type": "update_field",
        "payload": {"field_name": field_name, "field_value": field_value},
    })
    
    callback_task = params.result_callback({"status": "UPDATED"})
    
    await asyncio.gather(ui_task, callback_task)
    
    tool_duration = (time.time() - start_time) * 1000
    enhanced_perf_tracker.track_tool_performance(f"update_field_{field_name}", tool_duration)
    enhanced_perf_tracker.end_voice_interaction(voice_start, f"field_update_{field_name}")

async def handle_submit_form(rtvi: RTVIProcessor, params: FunctionCallParams):
    """Handles the submit_form tool call by sending a UI update message to the client
    and returning a result callback."""
    start_time = time.time()
    voice_start = enhanced_perf_tracker.start_voice_interaction()
    
    print(f"🏁 Submitting form...")
    
    ui_task = rtvi.send_server_message({
        "type": "submit_form", 
        "payload": {"status": "success"},
    })
    
    callback_task = params.result_callback({"status": "SUBMITTED"})
    
    await asyncio.gather(ui_task, callback_task)
    
    tool_duration = (time.time() - start_time) * 1000
    enhanced_perf_tracker.track_tool_performance("submit_form", tool_duration)
    enhanced_perf_tracker.end_voice_interaction(voice_start, "form_submission")