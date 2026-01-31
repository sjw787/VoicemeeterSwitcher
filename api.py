from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import voicemeeterlib
from main import VoicemeeterSettingsSwitcher

app = FastAPI(title="Voicemeeter Control API")

# Enable CORS for phone access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProfileRequest(BaseModel):
    profile_name: str

# Initialize the switcher
switcher = VoicemeeterSettingsSwitcher()

@app.get("/")
def root():
    """API root endpoint"""
    return {
        "name": "Voicemeeter Control API",
        "version": "1.0",
        "endpoints": [
            "/api/profiles",
            "/api/profile/load",
            "/api/profile/cycle",
            "/api/status"
        ]
    }

@app.get("/api/profiles")
def get_profiles():
    """Get list of available profiles"""
    profiles = [
        {
            "filename": f.name,
            "display_name": f.stem.split('-', 1)[1] if f.stem[0].isdigit() and '-' in f.stem else f.stem,
            "index": i
        }
        for i, f in enumerate(switcher.settings_files)
    ]
    return {
        "profiles": profiles,
        "current_index": switcher.current_index,
        "total": len(profiles)
    }

@app.post("/api/profile/load")
def load_profile(request: ProfileRequest):
    """Load a specific profile by filename"""
    try:
        # Find the profile file
        profile_path = None
        profile_index = None

        for i, f in enumerate(switcher.settings_files):
            if f.name == request.profile_name:
                profile_path = f
                profile_index = i
                break

        if profile_path is None:
            raise HTTPException(status_code=404, detail=f"Profile not found: {request.profile_name}")

        # Update the current index
        switcher.current_index = profile_index
        switcher._save_index()

        # Load the profile
        with voicemeeterlib.api('potato') as vmr:
            success = switcher.load_setting(vmr, profile_path)

        if success:
            display_name = profile_path.stem.split('-', 1)[1] if profile_path.stem[0].isdigit() and '-' in profile_path.stem else profile_path.stem
            return {
                "status": "success",
                "message": f"Loaded {display_name}",
                "profile": request.profile_name
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to load profile")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/profile/cycle")
def cycle_profile():
    """Cycle to the next profile"""
    try:
        with voicemeeterlib.api('potato') as vmr:
            success = switcher.cycle_next(vmr)

        if success:
            current_file = switcher.settings_files[switcher.current_index]
            display_name = current_file.stem.split('-', 1)[1] if current_file.stem[0].isdigit() and '-' in current_file.stem else current_file.stem
            return {
                "status": "success",
                "message": f"Switched to {display_name}",
                "current_profile": current_file.name,
                "current_index": switcher.current_index
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to cycle profile")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/status")
def get_status():
    """Get current status"""
    current_file = switcher.settings_files[switcher.current_index] if switcher.settings_files else None

    if current_file:
        display_name = current_file.stem.split('-', 1)[1] if current_file.stem[0].isdigit() and '-' in current_file.stem else current_file.stem
        return {
            "status": "running",
            "current_profile": current_file.name,
            "current_display_name": display_name,
            "current_index": switcher.current_index,
            "total_profiles": len(switcher.settings_files),
            "settings_dir": str(switcher.settings_dir)
        }
    else:
        return {
            "status": "running",
            "current_profile": None,
            "message": "No profiles available"
        }
