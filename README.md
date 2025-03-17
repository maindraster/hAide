
![](./haide.png)

<p align="center"><a href="https://www.indratang.top/product/haide">中文版</a> • <a href="#installation">Install</a> • <a href="#usage">Usage</a></p>

# hAide

Hiden AI supports chatting anywhere you write.

> This is a work of vibe codeing😅

## Installation

### Setup.exe

After downloading the installer, select the location and keep clicking "Next" - it's straightforward (by default, it creates a desktop shortcut). After double-clicking to run, right-click the system tray icon to configure your API KEY or local model settings. I won't elaborate too much here as there are plenty of notes in the configuration.

All configuration changes except hotkeys take effect immediately and will be used for each subsequent call.

Hotkey changes require exiting and reopening the application to take effect.

### Python

1. Find a way to install Python (minimum version unknown, I'm using 3.12)
2. Install the required libraries (I used pip install)
3. Run `haide.py` (it's just one Python file)

When you run it, you'll see a bunch of garbage printed - don't worry about it, that was just test output I wrote 💩. The code has lots of exception logger outputs that you can have AI help you remove.

If you want to package the Python code into a desktop application like I did, you can use `nuitka`:

```cmd
python -m nuitka --standalone --onefile --output-dir=dist --windows-disable-console --output-filename=haide.exe --windows-icon-from-ico=haide.ico --nofollow-import-to=torch,matplotlib,pandas,numpy,scipy,tkinter --follow-import-to=PIL.Image.Image --follow-import-to=PIL.Image.new --follow-import-to=PIL.ImageDraw.Draw --follow-import-to=keyboard.add_hotkey --follow-import-to=keyboard.remove_hotkey --follow-import-to=keyboard.unhook_all --follow-import-to=pyperclip.copy --follow-import-to=pyperclip.paste --follow-import-to=pyautogui.hotkey --follow-import-to=pyautogui.press --follow-import-to=pyautogui.click --follow-import-to=win32gui.GetWindowText --follow-import-to=win32gui.GetForegroundWindow --follow-import-to=win32gui.FindWindow --follow-import-to=win32gui.ShowWindow --follow-import-to=wxauto.WeChat --follow-import-to=openai.OpenAI --follow-import-to=pystray.Icon --follow-import-to=pystray.MenuItem --follow-import-to=uiautomation.WindowControl --follow-import-to=uiautomation.UIAutomationInitializerInThread --follow-import-to=comtypes.CoInitialize --follow-import-to=comtypes.CoUninitialize --follow-import-to=requests.post haide.py
```

Many of these `--follow-import-to` flags are incorrect and will generate WARNINGS. If you want to enable terminal testing, remove `--windows-disable-console`.

The generated .exe is in the dist folder, but running it there will cause errors. You need to move it to the root directory since the code looks for the Prompt folder and config file relative to the exe location. Of course, this is just my method - you can also try:
- Pyinstaller: Too slow in my testing
- Py2exe

Additionally, if you want to create a Setup installer for this application, you can check the `setup.iss` code and install `Inno Setup` to run it. But that's just my approach.

## Usage

### System Tray Background Running

Double-click to use, and you'll see it in the bottom-right system tray. Right-click menu allows for configuration.

Testing shows it uses about 83MB of memory (not including local model running).

### Hotkey Quick Access

Two default hotkeys:
- `ctrl+.` **Replace Mode**: Takes selected text as AI input (with preset prompt for WeChat assistant). If no text is selected, uses all text. AI output **replaces the selected text or all text**.
- `ctrl+/` **Append Mode**: Takes selected text as AI input (with preset prompt for WeChat assistant). If no text is selected, uses all text. AI output is **added on a new line after the selected text or cursor position**.

> AI output position follows the cursor location.

Just two hotkeys - minimalist design suitable for writing scenarios, no need to take hands off the keyboard.

### WeChat Chat Assistant

Automatically captures chat partner names from WeChat windows and matches them with preset prompts (`.md` files in the Prompts folder) to assist in modifying chat responses.

> New prompts must be created following the format `Chat Window Display Name.md`, like the included `临廊星.md` example. You can create a txt file and change its name and extension.
>
> For group chats, add a space, parentheses, and member count (this means it won't trigger if the count doesn't match - I was too lazy to change the code as it was intended for individual prompts), e.g., `守护最好的涵神❄️ (23)`

### AI Dialogue Anywhere with Text Input

The code works by simulating hotkeys like `ctrl+a`, `ctrl+c` to get input. It works anywhere these hotkeys are supported.

While you can send selected content to AI when reading documents, you can't ask questions without a place to type, so it's not ideal for that use case.

Main use cases are typing locations like Word, PPT, Notepad, search boxes, etc. You can even use it to optimize your prompts for web-based AI.

### Supported AI Models

Supports both API KEY and local model approaches.
- API KEY: Tested working with Silicon Flow API KEY
- Local Models: Tested working with `LM Studio` local server, `qwen2.5-coder-3b-instruct` and `qwen2.5-coder-3b-instruct` (due to same JSON format)

Of course, if you're using these basic local models, you'll get basic responses - 14B models are more capable. And if you can use QwQ 32B, that would be excellent.
