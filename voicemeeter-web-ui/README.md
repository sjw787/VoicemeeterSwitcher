# Voicemeeter Web UI

A modern Next.js web application for controlling Voicemeeter audio profiles.

## Features

- 🎵 View all available audio profiles
- ✅ See which profile is currently active
- 🔄 Switch between profiles with one click
- ⏭️ Quick cycle to the next profile
- 📱 Responsive design - works on desktop, tablet, and mobile
- 🔄 Auto-refresh every 2 seconds

## Prerequisites

1. Make sure the Voicemeeter API server is running:
   ```bash
   cd C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher
   run_api.bat
   ```

2. The API should be running at `http://localhost:8080`

## Getting Started

### Development Mode

1. Install dependencies (only needed once):
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:3100](http://localhost:3100) in your browser

### Production Build

1. Build the application:
   ```bash
   npm run build
   ```

2. Start the production server:
   ```bash
   npm start
   ```

## Configuration

Edit `.env.local` to change the API URL:

```env
NEXT_PUBLIC_API_URL=http://localhost:8080
```

To access from other devices on your network, change it to:

```env
NEXT_PUBLIC_API_URL=http://YOUR-COMPUTER-NAME.local:8080
```

Or use your IP address:

```env
NEXT_PUBLIC_API_URL=http://192.168.1.100:8080
```

## Usage

### Desktop/Laptop
Simply open the web app in any browser at `http://localhost:3100`

### Mobile Access
1. Make sure your phone is on the same WiFi network
2. Find your computer's name or IP address
3. Open the web app at `http://YOUR-COMPUTER-NAME.local:3100` or `http://192.168.1.100:3100`

### Switching Profiles
- Click on any profile card to switch to that profile
- Use the "Cycle to Next Profile" button to cycle through profiles in order
- The active profile is highlighted in green with a pulsing indicator

## Tech Stack

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe code
- **Tailwind CSS** - Modern styling
- **React Hooks** - State management
- **Fetch API** - Communication with backend

## File Structure

```
voicemeeter-web-ui/
├── app/
│   ├── layout.tsx       # Root layout
│   ├── page.tsx         # Main page with profile management
│   └── globals.css      # Global styles
├── components/
│   ├── ProfileCard.tsx  # Individual profile card
│   └── StatusBar.tsx    # Status display bar
├── types/
│   └── index.ts         # TypeScript type definitions
├── .env.local           # Environment variables
└── package.json         # Dependencies
```

## Troubleshooting

### Can't connect to API
- Make sure `run_api.bat` is running
- Check that port 8080 is not blocked by firewall
- Verify the API URL in `.env.local`

### Mobile can't access
- Ensure both devices are on the same network
- Add firewall rule for port 3100:
  ```powershell
  New-NetFirewallRule -DisplayName "Next.js Dev Server" -Direction Inbound -LocalPort 3100 -Protocol TCP -Action Allow
  ```

### Styles not showing
- Try clearing the browser cache
- Run `npm run build` and restart the server
