import os
import time
import sys
import threading
import winreg
from PIL import Image, ImageDraw
from keyboard import add_hotkey
from pyperclip import copy, paste
from pyautogui import hotkey, press, click
from win32gui import GetWindowText, GetForegroundWindow, FindWindow, ShowWindow
from logging import basicConfig, getLogger, INFO
from wxauto import WeChat
from openai import OpenAI
from pystray import Icon, MenuItem
from importlib.util import spec_from_file_location, module_from_spec
import uiautomation as uia
from comtypes import CoInitialize, CoUninitialize
from requests import post  # 添加requests模块用于本地模型通信
from json import dumps, loads  # 添加json模块用于处理请求和响应
import time

# 全局变量，记录配置文件的最后修改时间
config_last_modified = 0
def get_installation_dir():
    """获取程序的安装目录"""
    return os.path.dirname(os.path.abspath(sys.argv[0]))

# 获取安装目录
install_dir = get_installation_dir()

# 设置各个路径
config_path = os.path.join(install_dir, 'config.py')
prompts_path = os.path.join(install_dir, 'prompts')
logs_path = os.path.join(install_dir, 'logs')

# 创建必要的目录
os.makedirs(prompts_path, exist_ok=True)
os.makedirs(logs_path, exist_ok=True)

# 路径字典
paths = {
    'config': config_path,
    'prompts': prompts_path,
    'logs': logs_path
}

# 配置日志
log_file = os.path.join(logs_path, 'chat_modifier.log')
basicConfig(
    level=INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=log_file,
    filemode='a'
)
logger = getLogger(__name__)

def load_config():
    """加载配置文件，并更新全局变量"""
    global DEEPSEEK_API_KEY, MAX_TOKEN, TEMPERATURE, MODEL, DEEPSEEK_BASE_URL
    global LOCAL_MODEL_URL, LOCAL_MODEL_NAME, model_type, REPLACE_HOTKEY, APPEND_HOTKEY
    global client, config_last_modified, config
    
    # 记录配置文件的最后修改时间
    config_last_modified = os.path.getmtime(config_path)
    
    # 加载配置
    spec = spec_from_file_location("config", config_path)
    config = module_from_spec(spec)
    spec.loader.exec_module(config)
    
    # 从配置文件获取参数
    DEEPSEEK_API_KEY = config.DEEPSEEK_API_KEY
    MAX_TOKEN = config.MAX_TOKEN
    TEMPERATURE = config.TEMPERATURE
    MODEL = config.MODEL
    DEEPSEEK_BASE_URL = config.DEEPSEEK_BASE_URL
    
    # 初始化OpenAI客户端
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL
    )
    
    # 添加本地模型配置
    LOCAL_MODEL_URL = config.LOCAL_MODEL_URL
    LOCAL_MODEL_NAME = config.LOCAL_MODEL_NAME
    model_type = config.MODEL_TYPE
    REPLACE_HOTKEY = config.REPLACE_HOTKEY
    APPEND_HOTKEY = config.APPEND_HOTKEY
    
    logger.info("配置文件加载成功")
    print("配置文件加载成功")
    return True

def check_config_changed():
    """检查配置文件是否有变化，如有则重新加载"""
    global config_last_modified
    
    current_mtime = os.path.getmtime(config_path)
    if current_mtime > config_last_modified:
        load_config()
        return True
    return False

class WeChatHelper:
    def __init__(self):
        """初始化微信助手
        
        Args:
            language: 微信语言版本，默认简体中文'cn'
                     'cn': 简体中文
                     'cn_t': 繁体中文
                     'en': 英文
        """
        # 不再在初始化时强制要求微信窗口存在
        self.main_window = None
        self.nav_box = None
        self.session_box = None
        self.chat_box = None
        self.uia_initializer = None

    def initialize_window(self):
        """初始化微信窗口和控件"""
        try:
            # 初始化COM
            if self.uia_initializer is None:
                CoInitialize()  # 修改这里，使用CoInitialize()
                self.uia_initializer = uia.UIAutomationInitializerInThread()
            
            # 获取微信主窗口
            self.main_window = uia.WindowControl(ClassName='WeChatMainWndForPC', searchDepth=1)
            if not self.main_window.Exists():
                logger.warning("未找到微信窗口，请确保微信已登录并正在运行")
                return False
                
            # 显示窗口
            self._show_window()
            
            # 获取主要控件
            main_control = [i for i in self.main_window.GetChildren() if not i.ClassName][0]
            layout_control = main_control.GetFirstChildControl()
            
            # 获取三个主要区域：导航栏、会话列表、聊天区域
            self.nav_box, self.session_box, self.chat_box = layout_control.GetChildren()
            return True
        except Exception as e:
            logger.error(f"初始化微信窗口失败: {str(e)}")
            return False

    def _show_window(self):
        """显示微信窗口"""
        if self.main_window and self.main_window.Exists():
            hwnd = FindWindow('WeChatMainWndForPC', None)
            if hwnd:
                ShowWindow(hwnd, 1)  # 1表示正常显示
                self.main_window.SwitchToThisWindow()

    def get_current_chat_name(self) -> str:
        """获取当前正在聊天的对象名称"""
        try:
            # 确保窗口已初始化
            if not self.main_window or not self.main_window.Exists():
                if not self.initialize_window():
                    return ""
            
            # 检查聊天区域是否存在
            if not self.chat_box or not self.chat_box.Exists():
                return ""
            
            # 尝试获取聊天标题控件
            chat_title = self.chat_box.TextControl()
            if chat_title.Exists():
                return chat_title.Name
                
            # 备选方案：通过消息列表名称获取
            message_list = self.chat_box.ListControl()
            if message_list.Exists():
                list_name = message_list.Name
                # 处理"与xxx的聊天"或"xxx的聊天记录"格式
                if list_name.startswith('与') and list_name.endswith('的聊天'):
                    return list_name[1:-3]
                elif list_name.endswith('的聊天记录'):
                    return list_name[:-5]
            
            return ""
            
        except Exception as e:
            logger.error(f"获取聊天对象名称失败: {str(e)}")
            return ""

    def is_chatting(self) -> bool:
        """检查是否有打开的聊天窗口"""
        try:
            # 确保窗口已初始化
            if not self.main_window or not self.main_window.Exists():
                if not self.initialize_window():
                    return False
                    
            return bool(self.chat_box and self.chat_box.Exists() and self.chat_box.BoundingRectangle.width())
        except:
            return False

processing_lock = threading.Lock()
is_processing = False
load_config()
wechat = WeChatHelper()

def get_chat_partner_name(window_title):
    """从微信窗口标题中提取聊天对象名称"""
    # 微信聊天窗口标题通常是"聊天对象名称"
    # 检查是否在聊天
    chat_name = wechat.get_current_chat_name()
    if chat_name:
        return chat_name
    else:
        print("未能获取到聊天对象名称")
    return ""
        # 获取当前聊天对象

def is_wechat_window(window_title):
    """判断当前窗口是否是微信窗口"""
    # 微信窗口标题通常包含"微信"或者是特定的格式
    wechat_window = FindWindow('WeChatMainWndForPC', None)
    active_window = GetForegroundWindow()
    
    # 检查当前活跃窗口是否是微信窗口
    if wechat_window and wechat_window == active_window:
        return True
        
    # 备用方案：通过标题判断
    if "微信" in window_title:
        return True
        
    return False

def get_active_window_title():
    """获取当前活跃窗口的标题"""
    return GetWindowText(GetForegroundWindow())

def get_prompt_for_user(user_name):
    """根据用户名获取对应的prompt内容"""
    # 修改这里，使用paths字典
    print(user_name)
    prompt_path = os.path.join(paths['prompts'], f'{user_name}.md')
    
    if not os.path.exists(prompt_path):
        logger.warning(f"未找到用户 {user_name} 的prompt文件")
        return None
    else :
        print(f"找到用户 {user_name} 的prompt文件")

    try:
        with open(prompt_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"读取prompt文件失败: {str(e)}")
        return None

def modify_text_with_ai(text, prompt):
    """使用AI修改文本内容"""
    try:
        logger.info(f"调用AI修改文本")
        print(f"{prompt}")
        check_config_changed()
        # 根据模型类型选择处理方式
        if model_type == "LOCAL":
            # 使用本地模型处理
            return process_text_with_local_model(text, prompt)
        else:
            # 使用API处理
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "user", "content": f"你是一个聊天话术大师，以下是你要代入自己的聊天语境：\n{prompt}"},
                    {"role": "user", "content": f"然后请修改以下内容：\n{text}"}
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKEN,
                stream=False
            )
            
            if not response.choices:
                logger.error("API返回空choices")
                return text
            
            modified_text = response.choices[0].message.content.strip()
            logger.info(f"AI修改完成")
            
            return modified_text
    except Exception as e:
        logger.error(f"AI修改失败: {str(e)}")
        print(f"AI修改失败: {str(e)}")
        return text

def process_text_with_ai(text):
    """直接使用AI处理文本内容（作为prompt）"""
    try:
        logger.info(f"调用AI API处理文本")
        check_config_changed()
        # 根据模型类型选择处理方式
        if model_type == "LOCAL":
            # 使用本地模型处理
            return process_text_with_local_model(text)
        else:
            # 使用API处理
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "user", "content": text}
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKEN,
                stream=False
            )
            
            if not response.choices:
                logger.error("API返回空choices")
                return text
            
            result_text = response.choices[0].message.content.strip()
            logger.info(f"AI处理完成")
            
            return result_text
    except Exception as e:
        logger.error(f"AI处理失败: {str(e)}")
        print(f"AI处理失败: {str(e)}")
        return text

def process_text_with_local_model(text, prompt=None):
    """使用本地模型处理文本内容"""
    try:
        logger.info(f"调用本地模型处理文本")
        print(f"正在使用本地模型处理文本...")
        
        # 准备请求数据
        messages = []
        
        # 如果有prompt，添加system消息
        if prompt:
            messages.append({"role": "system", "content": prompt})
        
        # 添加用户消息
        messages.append({"role": "user", "content": text})
        
        # 准备请求体
        request_data = {
            "model": LOCAL_MODEL_NAME,
            "messages": messages,
            "temperature": TEMPERATURE,
            "max_tokens": -1,  # -1表示不限制
            "stream": False
        }
        
        # 发送请求
        response = post(
            LOCAL_MODEL_URL,
            headers={"Content-Type": "application/json"},
            data=dumps(request_data),
            timeout=60  # 设置超时时间
        )
        
        # 检查响应状态
        if response.status_code != 200:
            logger.error(f"本地模型返回错误状态码: {response.status_code}")
            print(f"本地模型返回错误: {response.text}")
            return text
        
        # 解析响应
        result = response.json()
        
        # 提取回复内容
        if "choices" in result and len(result["choices"]) > 0:
            # 获取message中的content字段
            if "message" in result["choices"][0] and "content" in result["choices"][0]["message"]:
                result_text = result["choices"][0]["message"]["content"].strip()
                logger.info(f"本地模型处理完成")
                return result_text
            else:
                logger.error("本地模型返回格式错误：message或content字段缺失")
                print("本地模型返回格式错误：message或content字段缺失")
                return text
        else:
            logger.error("本地模型返回格式错误")
            print("本地模型返回格式错误")
            return text
            
    except Exception as e:
        logger.error(f"本地模型处理失败: {str(e)}")
        print(f"本地模型处理失败: {str(e)}")
        return text

def replace_input_text(new_text):
    """替换输入框中的文本"""
    # 清空当前输入
    # hotkey('ctrl+a')
    # time.sleep(0.1)
    press('delete')
    time.sleep(0.1)
    
    # 输入新文本
    copy(new_text)
    hotkey('ctrl', 'v')
    logger.info("已替换输入文本")

def get_selected_text():
    """获取当前选中的文本"""
    # 复制当前选中的文本到剪贴板
    current_clipboard = paste()
    # 先清空剪贴板
    copy('')
    hotkey('ctrl', 'c')
    time.sleep(0.1)  # 等待复制操作完成
    selected_text = paste()
    
    # 如果没有选中文本，尝试获取输入框中的全部文本
    if not selected_text:
        hotkey('ctrl', 'a')
        time.sleep(0.1)
        hotkey('ctrl', 'c')
        time.sleep(0.1)
        selected_text = paste()
        # 恢复选择状态
        # click()
    
    return selected_text, current_clipboard

def on_hotkey_pressed():
    """当快捷键被按下时的处理函数"""
    global is_processing
    
    logger.info("快捷键被触发")
    
    with processing_lock:
        if is_processing:
            logger.info("正在处理中，请稍后再试")
            print("正在处理中，请稍后再试")
            return
        is_processing = True
    
    try:
        # 获取当前窗口标题
        window_title = get_active_window_title()
        
        # 检查是否是微信聊天窗口
        if not window_title:
            logger.warning("无法获取窗口标题")
            print("无法获取窗口标题")
            is_processing = False
            return
            
        # 判断当前窗口是否是微信窗口
        is_wechat = is_wechat_window(window_title)
        
        if is_wechat:
            # 微信窗口处理逻辑
            try:
                CoInitialize()
            except Exception as e:
                logger.error(f"COM初始化失败: {str(e)}")
                print(f"COM初始化失败: {str(e)}")
                is_processing = False
                return
            
            # 获取聊天对象名称
            chat_partner = get_chat_partner_name(window_title)
            if not chat_partner:
                logger.warning("未能获取到聊天对象名称")
                print("未能获取到聊天对象名称")
                is_processing = False
                return
                
            logger.info(f"当前聊天对象: {chat_partner}")
            print(f"当前聊天对象: {chat_partner}")
            
            # 获取prompt
            prompt = get_prompt_for_user(chat_partner)
            if not prompt:
                logger.warning(f"未找到用户 {chat_partner} 的prompt，使用默认prompt")
                print(f"未找到用户 {chat_partner} 的prompt，使用默认prompt")
                prompt = "你是一个文字修改助手，请帮助用户修改文字，使其更加得体、专业，同时保持原意。"
            
            # 获取选中的文本
            print("正在获取选中的文本...")
            selected_text, original_clipboard = get_selected_text()
            if not selected_text:
                logger.warning("未选中任何文本")
                print("未选中任何文本")
                copy(original_clipboard)  # 恢复剪贴板
                is_processing = False
                return
            
            print(f"获取到文本: {selected_text[:30]}...")
            
            # 显示处理提示
            print(f"\n正在处理文本，请稍候...\n")
            
            # 使用AI修改文本
            modified_text = modify_text_with_ai(selected_text, prompt)
            
            # 替换输入框中的文本
            print("正在替换输入框中的文本...")
            replace_input_text(modified_text)
            
            # 恢复剪贴板原内容
            copy(original_clipboard)
        else:
            # 非微信窗口处理逻辑
            print("检测到非微信窗口，将直接处理输入框内容...")
            
            # 获取输入框中的全部文本
            print("正在获取输入框文本...")
            selected_text, original_clipboard = get_selected_text()
            # if not selected_text:
            #     logger.warning("未获取到任何文本")
            #     print("未获取到任何文本")
            #     copy(original_clipboard)  # 恢复剪贴板
            #     is_processing = False
            #     return
            
            print(f"获取到文本: {selected_text[:30]}...")
            
            # 显示处理提示
            print(f"\n正在处理文本，请稍候...\n")
            
            # 使用AI处理文本
            result_text = process_text_with_ai(selected_text)
            
            # 替换输入框中的文本
            print("正在替换输入框中的文本...")
            replace_input_text(result_text)
            
            # 恢复剪贴板原内容
            copy(original_clipboard)
        
        print(f"\n文本已处理完成！\n")
        
    except Exception as e:
        logger.error(f"处理过程中发生错误: {str(e)}")
        print(f"处理过程中发生错误: {str(e)}")
    finally:
        # 释放COM
        try:
            CoUninitialize()
        except:
            pass
        is_processing = False

def on_hotkey_append_pressed():
    """当Ctrl+/快捷键被按下时的处理函数，不替换原文本，而是在后面追加"""
    global is_processing
    
    logger.info("追加模式快捷键被触发")
    
    with processing_lock:
        if is_processing:
            logger.info("正在处理中，请稍后再试")
            print("正在处理中，请稍后再试")
            return
        is_processing = True
    
    try:
        # 获取当前窗口标题
        window_title = get_active_window_title()
        
        # 检查是否有窗口标题
        if not window_title:
            logger.warning("无法获取窗口标题")
            print("无法获取窗口标题")
            is_processing = False
            return
        
        # 获取输入框中的全部文本
        print("正在获取输入框文本...")
        selected_text, original_clipboard = get_selected_text()
        # if not selected_text:
        #     logger.warning("未获取到任何文本")
        #     print("未获取到任何文本")
        #     copy(original_clipboard)  # 恢复剪贴板
        #     is_processing = False
        #     return
        
        print(f"获取到文本: {selected_text[:30]}...")
        
        # 显示处理提示
        print(f"\n正在处理文本，请稍候...\n")
        
        # 使用AI处理文本
        result_text = process_text_with_ai(selected_text)
        
        # 在原文本后追加AI回复
        print("正在追加AI回复...")
        
        # 然后追加AI回复
        append_text = f"\n\n{result_text}"
        copy(append_text)
        press('end')  # 移动到末尾
        hotkey('ctrl', 'v')  # 粘贴AI回复
        
        # 恢复剪贴板原内容
        copy(original_clipboard)
        
        print(f"\n文本已追加完成！\n")
        
    except Exception as e:
        logger.error(f"处理过程中发生错误: {str(e)}")
        print(f"处理过程中发生错误: {str(e)}")
    finally:
        is_processing = False

def create_icon_image():
    """创建系统托盘图标"""
    icon_path = os.path.join(install_dir, 'haide.ico')
    
    return Image.open(icon_path)

def open_config_file():
    """打开配置文件"""
    try:
        install_dir = get_installation_dir()
        config_path = os.path.join(install_dir, 'config.py')
        
        if not os.path.exists(config_path):
            print(f"配置文件不存在: {config_path}")
            return
        os.startfile(config_path)
        print(f"已打开配置文件: {config_path}")
    except Exception as e:
        print(f"打开配置文件失败: {str(e)}")

def open_prompts_folder():
    """打开prompts文件夹"""
    try:
        install_dir = get_installation_dir()
        prompts_path = os.path.join(install_dir, 'prompts')
        
        if not os.path.exists(prompts_path):
            print(f"提示词目录不存在: {prompts_path}")
            return
        os.startfile(prompts_path)
        print(f"已打开提示文件夹: {prompts_path}")
    except Exception as e:
        print(f"打开提示文件夹失败: {str(e)}")

def exit_app():
    """退出应用程序"""
    icon.stop()
    os._exit(0)

def open_help_web():
    """打开帮助网页"""
    try:
        import webbrowser
        help_url = "https://indratang.top/product/haide"  # 设置帮助页面的URL
        webbrowser.open(help_url)
        print(f"已打开帮助网页: {help_url}")
    except Exception as e:
        print(f"打开帮助网页失败: {str(e)}")
        logger.error(f"打开帮助网页失败: {str(e)}")

def setup_tray():
    """设置系统托盘图标和菜单"""
    global icon
    
    # 创建菜单项
    menu = (
        MenuItem('配置文件设置', open_config_file),
        MenuItem('打开Prompts文件夹', open_prompts_folder),
        MenuItem('帮助', open_help_web),
        MenuItem('退出', exit_app)
    )
    
    # 创建系统托盘图标
    icon = Icon(
        "chat_modifier",
        create_icon_image(),
        "hAide",
        menu
    )
    
    # 在单独的线程中运行图标
    icon_thread = threading.Thread(target=icon.run)
    icon_thread.daemon = True
    icon_thread.start()

def main():
    try:
        # 设置更详细的日志记录
        print("程序启动中...")
        logger.info("程序启动")
        
        # 修改这里，使用paths字典
        os.makedirs(paths['prompts'], exist_ok=True)
        logger.info("创建必要目录完成")
        
        try:
            # 初始化COM环境（主线程）
            print("初始化COM环境...")
            CoInitialize()  # 修改这里，使用CoInitialize()
            logger.info("COM环境初始化完成")
        except Exception as e:
            logger.error(f"COM初始化失败: {str(e)}")
            print(f"COM初始化失败: {str(e)}")
        
        try:
            # 设置系统托盘
            print("设置系统托盘...")
            setup_tray()
            logger.info("系统托盘设置完成")
        except Exception as e:
            logger.error(f"设置系统托盘失败: {str(e)}")
            print(f"设置系统托盘失败: {str(e)}")
        
        print("微信聊天内容AI修改助手已启动")
        print("使用方法:")
        print("1. 在微信聊天窗口中输入要发送的内容")
        print("2. 按下Ctrl+P快捷键")
        print("3. AI将根据对应的prompt文件修改内容")
        print("4. 修改后的内容将替换原输入")
        print("\n不用管以上的东西，程序已在系统托盘中运行，右键点击图标可以访问菜单\n")
        
        try:
            # 注册快捷键
            print("注册快捷键...")
            # 先尝试取消已有的快捷键注册
            try:
                from keyboard import remove_hotkey, unhook_all
                remove_hotkey('ctrl+.')
                remove_hotkey('ctrl+/')
                unhook_all()  # 解除所有钩子，确保干净的状态
            except:
                pass
                
            # 注册Ctrl+P快捷键（替换模式）
            add_hotkey(REPLACE_HOTKEY, on_hotkey_pressed)
            print("快捷键注册完成: Ctrl+. (替换模式)")
            logger.info("快捷键注册完成: Ctrl+. (替换模式)")
            
            # 注册Ctrl+L快捷键（追加模式）
            add_hotkey(APPEND_HOTKEY, on_hotkey_append_pressed)
            print("快捷键注册完成: Ctrl+/ (追加模式)")
            logger.info("快捷键注册完成: Ctrl+/ (追加模式)")
        except Exception as e:
            logger.error(f"注册快捷键失败: {str(e)}")
            print(f"注册快捷键失败: {str(e)}")
        
        # 保持程序运行
        print("程序运行中，按Ctrl+C退出...")
        while True:
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n程序已退出")
    except Exception as e:
        logger.error(f"程序运行错误: {str(e)}")
        print(f"程序运行错误: {str(e)}")
        
        # 保持窗口不关闭，以便查看错误信息
        print("\n程序遇到错误，按Enter键退出...")
        input()
    finally:
        # 释放COM
        try:
            CoUninitialize()  # 修改这里，使用CoUninitialize()
        except:
            pass

# 添加一个简单的异常处理装饰器
def exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行出错: {str(e)}")
            print(f"函数 {func.__name__} 执行出错: {str(e)}")
            return None
    return wrapper

# 为关键函数添加异常处理装饰器
setup_tray = exception_handler(setup_tray)
on_hotkey_pressed = exception_handler(on_hotkey_pressed)

if __name__ == "__main__":
    main()
