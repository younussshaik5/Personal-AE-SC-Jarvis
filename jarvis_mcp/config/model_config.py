"""Model configuration - Maps skills and tasks to specific NVIDIA models."""

# Model Assignments
MODELS = {
    "text": "stepfun-ai/step-3-5-flash",
    "long_context": "nvidia/nemotron-3-super-120b-a12b",
    "reasoning": "kimi-k2-thinking",
    "audio": "nvidia/whisper-large-v3-turbo",
    "video": "nvidia/cosmos-reason2-8b",
    "quick": "nvidia/mistral-nemo-minitron-8b"
}

# Skill to Model Type Mapping
SKILL_MODEL_MAP = {
    # TEXT GENERATION SKILLS (text model)
    "proposal": "text",
    "discovery": "text",
    "meeting_prep": "text",
    "followup_email": "text",
    "battlecard": "text",
    "demo_strategy": "text",
    "sow": "text",
    "custom_template": "text",
    
    # LONG CONTEXT SKILLS (nemotron-3-super)
    "account_summary": "long_context",
    "risk_report": "long_context",
    "technical_risk": "long_context",
    "knowledge_builder": "long_context",
    "value_architecture": "long_context",
    "competitive_intelligence": "long_context",
    "competitor_pricing": "long_context",
    
    # REASONING SKILLS (kimi-k2-thinking)
    "evolution_optimizer": "reasoning",
    "conversation_analyzer": "reasoning",
    "outcome_predictor": "reasoning",
    "deal_stage_tracker": "reasoning",
    "meddpicc": "reasoning",
    
    # AUDIO SKILLS (whisper)
    "meeting_summary": "audio",
    "conversation_summarizer": "audio",
    
    # VIDEO SKILLS (cosmos-reason2)
    "architecture_diagram": "video",
    "html_generator": "video",
    
    # QUICK/LIGHTWEIGHT SKILLS (mistral-nemo)
    "quick_insights": "quick",
    "conversation_extractor": "quick",
}

# File Type to Model Mapping
FILE_MODEL_MAP = {
    ".pdf": "long_context",  # PDFs = long documents
    ".docx": "long_context",  # Word docs = long documents
    ".xlsx": "text",  # Excel = structured text
    ".pptx": "video",  # PowerPoint = visual
    ".txt": "text",  # Text files = text model
    ".json": "text",  # JSON = text model
    ".mp3": "audio",  # Audio = audio model
    ".wav": "audio",  # Audio = audio model
    ".mp4": "video",  # Video = video model
    ".mov": "video",  # Video = video model
}

# Task Type to Model Mapping
TASK_MODEL_MAP = {
    # Learning tasks
    "vectorize_document": "long_context",
    "extract_insights": "reasoning",
    "analyze_conversation": "reasoning",
    "predict_outcome": "reasoning",
    
    # Content generation
    "generate_proposal": "text",
    "generate_discovery": "text",
    "generate_battlecard": "text",
    "generate_sow": "text",
    
    # Analysis
    "analyze_risk": "reasoning",
    "analyze_bottleneck": "reasoning",
    "analyze_effectiveness": "reasoning",
    
    # Transcription/Media
    "transcribe_meeting": "audio",
    "analyze_video": "video",
    "generate_demo_flow": "video",
    
    # Quick tasks
    "quick_lookup": "quick",
    "quick_summary": "quick",
}

def get_model_for_skill(skill_name: str) -> str:
    """Get the NVIDIA model for a specific skill."""
    model_type = SKILL_MODEL_MAP.get(skill_name, "text")
    return MODELS.get(model_type, MODELS["text"])

def get_model_for_file(file_extension: str) -> str:
    """Get the NVIDIA model for processing a file type."""
    model_type = FILE_MODEL_MAP.get(file_extension.lower(), "text")
    return MODELS.get(model_type, MODELS["text"])

def get_model_for_task(task_type: str) -> str:
    """Get the NVIDIA model for a specific task."""
    model_type = TASK_MODEL_MAP.get(task_type, "text")
    return MODELS.get(model_type, MODELS["text"])

def get_model_type_for_skill(skill_name: str) -> str:
    """Get the model type (category) for a skill."""
    return SKILL_MODEL_MAP.get(skill_name, "text")

def get_all_models() -> dict:
    """Get all available models."""
    return MODELS.copy()

def get_skill_assignments() -> dict:
    """Get all skill-to-model assignments."""
    return SKILL_MODEL_MAP.copy()

# Display mapping
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🤖 JARVIS NVIDIA MODEL CONFIGURATION")
    print("="*70)
    
    print("\n📋 AVAILABLE MODELS:")
    for model_type, model_id in MODELS.items():
        print(f"  {model_type:15} → {model_id}")
    
    print("\n🎯 SKILL ASSIGNMENTS:")
    for skill, model_type in sorted(SKILL_MODEL_MAP.items()):
        model_id = MODELS[model_type]
        print(f"  {skill:25} → {model_type:15} ({model_id})")
    
    print("\n📁 FILE TYPE ASSIGNMENTS:")
    for file_type, model_type in sorted(FILE_MODEL_MAP.items()):
        model_id = MODELS[model_type]
        print(f"  {file_type:10} → {model_type:15} ({model_id})")
    
    print("\n✅ Configuration Complete\n")
