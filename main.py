"""
Voicemeeter Settings Switcher
Cycles through saved Voicemeeter settings files (.xml)
"""

import voicemeeterlib
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from winotify import Notification, audio
    HAS_NOTIFICATIONS = True
except ImportError:
    HAS_NOTIFICATIONS = False


def get_resource_path(filename):
    """Get the correct path for bundled resources (inside exe)."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return str(Path(sys._MEIPASS) / filename)
    else:
        # Running as script
        return str(Path(__file__).parent / filename)


def get_app_dir():
    """Get the directory where the exe/script is located (for persistent files)."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe - use exe's directory
        return Path(sys.executable).parent
    else:
        # Running as script
        return Path(__file__).parent

def show_notification(title, message, timeout=1):
    if HAS_NOTIFICATIONS:
        try:
            toast = Notification(
                app_id="Voicemeeter Switcher",
                title=title,
                msg=message,
                icon=get_resource_path("VoicemeeterLogo_72x72.ico")
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
        except Exception:
            pass




class VoicemeeterSettingsSwitcher:
    def __init__(self, settings_dir=None):
        """Initialize the Voicemeeter settings switcher."""
        app_dir = get_app_dir()
        self.settings_dir = Path(settings_dir) if settings_dir else app_dir / "settings"
        self.settings_dir.mkdir(exist_ok=True)

        self.state_file = app_dir / ".current_index"
        self.settings_files = sorted(self.settings_dir.glob("*.xml"))

        if not self.settings_files:
            print(f"No .xml settings files found in {self.settings_dir}")
            print("Please save your Voicemeeter settings to this directory.")
            sys.exit(1)

        self.current_index = self._load_index()

    def _load_index(self):
        """Load the last used index from state file."""
        try:
            if self.state_file.exists():
                index = int(self.state_file.read_text().strip())
                if 0 <= index < len(self.settings_files):
                    return index
        except:
            pass
        return 0

    def _save_index(self):
        """Save the current index to state file."""
        try:
            self.state_file.write_text(str(self.current_index))
        except Exception as e:
            print(f"Warning: Could not save state: {e}")

    def load_setting(self, vmr, file_path):
        """Load a specific settings file."""
        print(f"Loading settings from: {file_path.name}")

        # Map XML type attribute to API device type
        # type='1' = mme, type='3' = ks, type='4' = wdm, type='5' = asio
        type_map = {
            '1': 'mme',
            '3': 'ks',
            '4': 'wdm',
            '5': 'asio',
        }

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Process OutputDev settings - change hardware output device assignments
            for output_elem in root.findall(".//OutputDev[@index]"):
                try:
                    index = int(output_elem.get('index')) - 1
                    device_name = output_elem.get('name', '')
                    device_type = output_elem.get('type', '1')  # Default to MME

                    if 0 <= index < len(vmr.bus):
                        api_type = type_map.get(device_type, 'wdm')

                        # If device is "-" or empty, unset it by sending empty string
                        if not device_name or device_name == '-':
                            print(f"  Unsetting A{index + 1} output device")
                            setattr(vmr.bus[index].device, api_type, "")
                        else:
                            print(f"  Setting A{index + 1} output device ({api_type}): {device_name}")
                            setattr(vmr.bus[index].device, api_type, device_name)
                        time.sleep(0.3)
                except Exception as e:
                    print(f"  Warning: Could not set output device {index + 1}: {e}")

            # Process InputDev settings - change hardware input device assignments
            for input_elem in root.findall(".//InputDev[@index]"):
                try:
                    index = int(input_elem.get('index')) - 1
                    device_name = input_elem.get('name', '')
                    device_type = input_elem.get('type', '1')  # Default to MME

                    if 0 <= index < len(vmr.strip):
                        api_type = type_map.get(device_type, 'wdm')

                        # If device is "-" or empty, unset it by sending empty string
                        if not device_name or device_name == '-':
                            print(f"  Unsetting input {index + 1} device")
                            setattr(vmr.strip[index].device, api_type, "")
                        else:
                            print(f"  Setting input {index + 1} device ({api_type}): {device_name}")
                            setattr(vmr.strip[index].device, api_type, device_name)
                        time.sleep(0.3)
                except Exception as e:
                    print(f"  Warning: Could not set input device {index + 1}: {e}")

            # Give Voicemeeter extra time to apply all settings and stabilize
            # Increased to prevent crashes
            time.sleep(2.5)
            print(f"\nSettings applied from {file_path.name}")
            return True

        except Exception as e:
            print(f"\nError loading settings from {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def cycle_next(self, vmr):
        """Cycle to the next settings file."""
        if not self.settings_files:
            print("No settings files available.")
            return False

        self.current_index = (self.current_index + 1) % len(self.settings_files)
        self._save_index()

        next_file = self.settings_files[self.current_index]

        # Get a friendly name from the filename (remove number prefix and extension)
        friendly_name = next_file.stem
        if friendly_name[0].isdigit() and '-' in friendly_name:
            friendly_name = friendly_name.split('-', 1)[1]

        print(f"\nSwitching to setting {self.current_index + 1}/{len(self.settings_files)}")

        # Show notification
        show_notification(
            "Voicemeeter Profile",
            f"Switched to: {friendly_name}",
            timeout=1
        )

        return self.load_setting(vmr, next_file)

    def list_settings(self):
        """List all available settings files."""
        print(f"Available settings ({len(self.settings_files)} files):")
        for i, file in enumerate(self.settings_files, 1):
            marker = " <- Current" if i - 1 == self.current_index else ""
            print(f"  {i}. {file.name}{marker}")


def main():
    """Main function - cycles to the next setting."""
    print("=== Voicemeeter Settings Switcher ===\n")

    switcher = VoicemeeterSettingsSwitcher()

    if len(switcher.settings_files) == 0:
        return

    try:
        with voicemeeterlib.api('potato') as vmr:
            print(f"Connected to Voicemeeter {vmr.type}\n")
            switcher.list_settings()
            switcher.cycle_next(vmr)
            print("\nDone!")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
