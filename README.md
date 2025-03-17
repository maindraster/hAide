
![](./haide.png)

## 安装方法

### 安装包

下载安装包之后，选位置，一直下一步即可，没什么难度（默认桌面创建快捷方式）。双击运行之后，托盘右键配置一下你自己的 API KEY 或本地模型的配置，我这里不过多赘述，那里面的备注写了不少。

除了快捷键以外所有配置更改是即时，即每次调用都会用最新更改后的配置。

快捷键更改需要退出，重新打开使用才行。

### 源码安装

1. 自己想办法安装个 Python （最低版本要求未知，我用的3.12）
2. 自己想办法把需要的库安装好（我用的 pip install）
3. 运行`haide.py`（本来就一个Python文件）

运行你就会看到里面print了一堆垃圾，不要在意，那时我为了测试写的💩。整个代码有大量大量的exception logger输出，你可以让 AI 帮你全删了。

如果你也想要把 Python 打包成一个电脑端应用，可以像我一样使用`nuitka`：

```cmd
python -m nuitka --standalone --onefile --output-dir=dist --windows-disable-console --output-filename=haide.exe --windows-icon-from-ico=haide.ico --nofollow-import-to=torch,matplotlib,pandas,numpy,scipy,tkinter --follow-import-to=PIL.Image.Image --follow-import-to=PIL.Image.new --follow-import-to=PIL.ImageDraw.Draw --follow-import-to=keyboard.add_hotkey --follow-import-to=keyboard.remove_hotkey --follow-import-to=keyboard.unhook_all --follow-import-to=pyperclip.copy --follow-import-to=pyperclip.paste --follow-import-to=pyautogui.hotkey --follow-import-to=pyautogui.press --follow-import-to=pyautogui.click --follow-import-to=win32gui.GetWindowText --follow-import-to=win32gui.GetForegroundWindow --follow-import-to=win32gui.FindWindow --follow-import-to=win32gui.ShowWindow --follow-import-to=wxauto.WeChat --follow-import-to=openai.OpenAI --follow-import-to=pystray.Icon --follow-import-to=pystray.MenuItem --follow-import-to=uiautomation.WindowControl --follow-import-to=uiautomation.UIAutomationInitializerInThread --follow-import-to=comtypes.CoInitialize --follow-import-to=comtypes.CoUninitialize --follow-import-to=requests.post haide.py
```

这个命令行有好多`--follow-import-to`是不对的，会出 WARNING。另外如果你想要能弹出终端测试的话，删掉`--windows-disable-console`。

生成的.exe是在dist文件夹下，直接运行包报错的，你得移出来到根目录下，因为代码当中是根据exe相对位置来找 Prompt 文件夹和 config 配置文件。当然这只是我的方法，你还可以尝试：
- Pyinstaller: 亲测太慢了
- Py2exe

另外，如果你也想为这个应用制作一个 Setup 安装包。你可以查看`setup.iss`代码，安装一个叫`inno Setup`来跑他。当然这只是我的办法。

## 使用方法

### 托盘后台运行

双击即使用，打开右下角托盘即能看到。右键菜单可以进行一些配置。

实测后台占用 83M （不包含跑本地模型）左右内存。

### 快捷键便捷调用

默认设置两个快捷键：
- `ctrl+.`**替换模式**: 将选中的文字 AI 的输入（如果是微信辅助聊天则还有预设 prompt 作为输入）。如果没有选中任何文字，会直接选中所有文字的输入。获取到 AI 输出后**替换选中的文字或所有文字**。
- `ctrl+/`**补写模式**: 将选中的文字 AI 的输入（如果是微信辅助聊天则还有预设 prompt 作为输入）。如果没有选中任何文字，会直接选中所有文字的输入。获取到 AI 输出后**在选中的文字或光标所在行后换行输出**。

> 在 AI 输出结果的位置跟随光标位置。

只用两个快捷键，极简设计，适配写文章等打字场景，双手无须离开键盘。

### 微信聊天辅助功能

自动从微信窗口捕获聊天对象名称，与预设（Prompts文件夹下的`.md`）文件名称做匹配，获取文件当中的 prompt 来辅助修改聊天的话术。

> 新建的提示词必须按照`聊天窗口显示的对方名称.md`格式新建，比如安装包里自带的`临廊星.md`案例。比如你可以新建一个txt文件，改名称+改后缀。
>
> 如果是群聊，需要额外加一个空格、一对英文括号和群聊人数（这意味着人数不匹配就不会调用，代码懒得改，本来想的就是给单独的人设置 Prompt），比如：`守护最好的涵神❄️ (23)`

### 任意可打字地方与AI对话

代码依靠模拟按下快捷键`ctrl+a`、`ctrl+c`等的方式来实现获取输入。本质上能够实现这些快捷键的地方就能使用。

但是看文档的时候虽然可以把选中的内容给 AI ，通过移动光标到可以粘贴内容的地方，但是没办法提问，因此不太适用。

因此主要使用场景为打字的地方，比如 Word、PPT、记事本、搜索框等，甚至你可以让它帮你优化你给网页版AI 提问的 prompt。

### 支持的 AI 模型

支持 API KEY 和本地模型两种方式。
- API KEY: 使用硅基流动 API KEY 测试可行
- 本地模型: 使用 `LM Studio` 本地服务器，`qwen2.5-coder-3b-instruct`和`qwen2.5-coder-3b-instruct`测试可行（因为 json 格式相同）

当然你要是本地用的是这些垃圾模型，只能得到垃圾回答，14B 模型还差不多。当然如果你能用上 QwQ 32B 那就很爽了。
