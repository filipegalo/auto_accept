# Installation Guide - Auto-Accept Email Automation

This guide will help you install and run Auto-Accept on your Windows or Mac system.

## Prerequisites

- **Windows 10/11** or **macOS 11+**
- **Google Chrome** installed on your system
- **Gmail account** with app-specific password (for automation)
- **Account on your desired platform** (e.g., Smartcat)

---

## Option A: Download Pre-Built Executable (Easiest)

### For Windows Users:

1. **Download the executable**

   - Download `auto-accept.exe` from the releases page
   - Save it to a folder on your computer (e.g., `C:\Users\YourName\Desktop\auto-accept\`)

2. **Create credentials file** (optional, for security)

   - Create a folder called `.auto_accept` in your home directory:
     - Windows: `C:\Users\YourName\.auto_accept\`
   - This will store your configuration profiles securely

3. **Run the application**

   - Double-click `auto-accept.exe`
   - Or open Command Prompt and run:
     ```cmd
     cd path\to\auto-accept
     auto-accept.exe
     ```

4. **First Run Setup**

   - Select option `2. Create new profile`
   - Enter your Gmail credentials
   - Enter your platform credentials (e.g., Smartcat)
   - Configure email subject to scan for
   - (Optional) Configure button/element clicking
   - Save your profile

5. **Next Runs**
   - Run `auto-accept.exe`
   - Select option `1. Use existing profile`
   - Pick your profile from the list
   - Application will start scanning

---

### For Mac Users:

1. **Download the executable**

   - Download `auto-accept` from the releases page
   - Save it to a folder in your home directory (e.g., `~/auto-accept/`)

2. **Grant execute permission**

   - Open Terminal and run:
     ```bash
     chmod +x ~/auto-accept/auto-accept
     ```

3. **Create credentials folder** (optional)

   - Terminal will automatically create `~/.auto_accept/` folder
   - Your profiles will be stored there securely

4. **Run the application**

   - Open Terminal and run:
     ```bash
     ~/auto-accept/auto-accept
     ```
   - Or create an alias for easier access:
     ```bash
     alias auto-accept="~/auto-accept/auto-accept"
     auto-accept
     ```

5. **First Run Setup**

   - Same as Windows steps above

6. **Add to Applications** (optional)
   - Create a launcher script for easier access
   - See "Create Desktop Shortcut" section below

---

## Configuration Setup

### Getting Gmail App Password

Gmail doesn't allow regular passwords with Selenium. You need an app-specific password:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable "2-Step Verification" (if not already enabled)
3. Scroll down and select "App passwords"
4. Choose "Mail" and "Windows Computer" (or "Mac")
5. Google will generate a 16-character password
6. **Use this password in Auto-Accept**, not your regular Gmail password

### Creating Your First Profile

When you run the app for the first time:

```
Options:
  [1] Use existing profile
  [2] Create new profile
  [3] Exit

Select option (1/2/3): 2
```

Then follow the prompts:

1. **Gmail Email**: `your-email@gmail.com`
2. **Gmail Password**: Your app-specific password (16 characters)
3. **Platform**: Select from available options (e.g., Smartcat)
4. **Platform Email**: Your Smartcat email
5. **Platform Password**: Your Smartcat password
6. **Email Subject**: Text to search for (e.g., "Invoice")
7. **Button Clicking** (optional): Element text to click

Your profile is saved in:

- Windows: `C:\Users\YourName\.auto_accept\configs\profile-name.json`
- Mac: `~/.auto_accept/configs/profile-name.json`

---

Happy automating! 🚀
