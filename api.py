from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import voicemeeterlib
import time
import threading
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

# Mutex lock to prevent concurrent Voicemeeter operations
# This prevents crashes from simultaneous API calls
vmr_lock = threading.Lock()
last_operation_time = 0
MIN_DELAY_BETWEEN_OPERATIONS = 2.0  # Minimum 2 seconds between operations

def execute_with_vmr(operation_func):
    """
    Execute a Voicemeeter operation safely with proper locking and delays.
    This prevents crashes from concurrent or rapid operations.
    """
    global last_operation_time

    with vmr_lock:
        # Enforce minimum delay between operations
        time_since_last = time.time() - last_operation_time
        if time_since_last < MIN_DELAY_BETWEEN_OPERATIONS:
            sleep_time = MIN_DELAY_BETWEEN_OPERATIONS - time_since_last
            print(f"  Waiting {sleep_time:.1f}s before next operation...")
            time.sleep(sleep_time)

        # Create a fresh connection for this operation
        try:
            print("  Connecting to Voicemeeter...")
            with voicemeeterlib.api('potato') as vmr:
                print("  ✓ Connected")
                result = operation_func(vmr)
                print("  ✓ Operation complete")
                last_operation_time = time.time()
                return result
        except Exception as e:
            print(f"  ✗ Operation failed: {e}")
            last_operation_time = time.time()
            raise

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
        print(f"\nReceived request to load profile: {request.profile_name}")

        # Find the profile file
        profile_path = None
        profile_index = None

        for i, f in enumerate(switcher.settings_files):
            if f.name == request.profile_name:
                profile_path = f
                profile_index = i
                break

        if profile_path is None:
            print(f"Profile not found: {request.profile_name}")
            print(f"Available files: {[f.name for f in switcher.settings_files]}")
            raise HTTPException(status_code=404, detail=f"Profile not found: {request.profile_name}")

        print(f"Found profile at index {profile_index}: {profile_path.name}")

        # Update the current index
        switcher.current_index = profile_index
        switcher._save_index()

        # Load the profile safely with mutex locking
        def load_operation(vmr):
            return switcher.load_setting(vmr, profile_path)

        success = execute_with_vmr(load_operation)

        if success:
            display_name = profile_path.stem.split('-', 1)[1] if profile_path.stem[0].isdigit() and '-' in profile_path.stem else profile_path.stem
            print(f"✓ Successfully loaded profile: {display_name}\n")
            return {
                "status": "success",
                "message": f"Loaded {display_name}",
                "profile": request.profile_name
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to load profile - check Voicemeeter is running")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Exception while loading profile: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/profile/cycle")
def cycle_profile():
    """Cycle to the next profile"""
    try:
        print("\nReceived request to cycle profile")

        # Cycle safely with mutex locking
        def cycle_operation(vmr):
            return switcher.cycle_next(vmr)

        success = execute_with_vmr(cycle_operation)

        if success:
            current_file = switcher.settings_files[switcher.current_index]
            display_name = current_file.stem.split('-', 1)[1] if current_file.stem[0].isdigit() and '-' in current_file.stem else current_file.stem
            print(f"✓ Cycled to profile: {display_name}\n")
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
        print(f"Exception while cycling profile: {e}")
        import traceback
        traceback.print_exc()
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
