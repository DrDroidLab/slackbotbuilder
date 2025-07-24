from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import asyncio
from datetime import datetime
from slack_events import slack_event_handler
from slack_credentials_manager import credentials_manager
from workflow_manager import workflow_manager

app = FastAPI(title="AI Slack Bot Builder", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    credentials_summary = credentials_manager.get_credentials_summary()
    workflows_summary = workflow_manager.get_workflows_summary()
    return {
        "status": "healthy", 
        "message": "AI Slack Bot Builder is running",
        "credentials": credentials_summary,
        "workflows": workflows_summary
    }

# Slack Interactive endpoint
@app.post("/api/slack/interactive")
async def handle_slack_interactive(request: Request):
    """Handle Slack interactive components"""
    try:
        # For now, just return a success response
        # This can be expanded later for handling interactive components
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/slack/events")
async def handle_slack_events(request: Request, background_tasks: BackgroundTasks):
    """Handle Slack event subscriptions"""
    try:
        request_data = await request.json()
        
        # Return 200 immediately and process in background
        background_tasks.add_task(slack_event_handler.handle_event_async, request_data, request)
        return {"status": "accepted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000) 