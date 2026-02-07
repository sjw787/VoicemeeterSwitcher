export interface Profile {
  filename: string;
  display_name: string;
  index: number;
}

export interface Status {
  status: string;
  current_profile: string;
  current_display_name: string;
  current_index: number;
  total_profiles: number;
  settings_dir: string;
}

export interface VolumeInfo {
  bus: string;
  gain: number;
  bus_index: number;
}

