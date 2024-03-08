import gradio as gr
import requests
import re
import os
from pydub import AudioSegment  # 用于处理音频文件
import pyaudio  # 用于播放音频
from datetime import datetime

# 语音合成
TTS_API_URL = "http://192.168.50.63:5000/tts"

global p,streamAudio
p = pyaudio.PyAudio()
streamAudio = None

# 定义 default_text
default_text = (
    "那年五月至第二年的年初，我住在一条狭长山谷入口附近的山顶上。夏天，山谷深处雨一阵阵下个不停，"
    "而山谷外面大体是白云蓝天——那是海上有西南风吹来的缘故。风带来的湿乎乎的云进入山谷，"
    "顺着山坡往上爬时就让雨降了下来。房子正好建在其分界线那里，所以时不时出现这一情形："
    "房子正面一片明朗，而后院却大雨如注。起初觉得相当不可思议，但不久习惯之后，反倒以为理所当然。"
    "周围山上低垂着时断时续的云。每当有风吹来，那样的云絮便像从前世入此间的魂灵一样为寻觅失去的记忆而在山间飘忽不定。"
    "看上去宛如细雪的白亮亮的雨，有时也悄无声息地随风起舞。差不多总有风吹来，没有空调也能大体快意地度过夏天。"
)

def safe_filename(text, max_length=50):
    # 移除或替换文件名中不允许的字符
    safe_text = re.sub(r'[\\/*?:"<>|]', "", text)
    # 限制文件名长度，防止过长
    if len(safe_text) > max_length:
        safe_text = safe_text[:max_length - 3] + "..."
    return safe_text

def text_to_speech(text, index, output_dir, subtitle_base_name, chaName, characterEmotion="default",
                   textLanguage="多语种混合", topK=40, topP=0.9, temperature=0.7,stream="False",save_temp="False"):
    # 构造请求体，使用函数参数
    body = {
        "text": text,
        "cha_name": chaName,
        "text_language": textLanguage,
        "top_k": topK,
        "top_p": topP,
        "temperature": temperature,
        "character_emotion": characterEmotion,
        "stream": stream,
        "save_temp": save_temp
    }

    # 发送POST请求
    response = requests.post(TTS_API_URL, json=body)

    # 处理响应
    if response.status_code == 200:
        # 安全处理字幕文本，用于文件名
        safe_text = safe_filename(text)
        audio_file_name = f"{chaName}_{subtitle_base_name}_audio_{str(index).zfill(3)}_{safe_text}.wav"
        audio_file_path = os.path.join(output_dir, audio_file_name)
        with open(audio_file_path, "wb") as audio_file:
            audio_file.write(response.content)
        return audio_file_path
    else:
        print(f"Error: Failed to generate speech for text: '{text}' with status code: {response.status_code}")
        return None

#创建第二个 text_to_speech 函数来处理 txt 文件转换为音频的需求
def text_to_speech_txt(text, output_dir, text_base_name, chaName, characterEmotion="default", textLanguage="多语种混合",
                   topK=40, topP=0.9, temperature=0.7,stream="False",save_temp="False"):
    # 构造请求体，使用函数参数
    body = {
        "text": text,
        "cha_name": chaName,
        "text_language": textLanguage,
        "top_k": topK,
        "top_p": topP,
        "temperature": temperature,
        "character_emotion": characterEmotion,
        "stream": stream,
        "save_temp": save_temp
    }

    # 发送POST请求
    response = requests.post(TTS_API_URL, json=body)

    # 处理响应
    if response.status_code == 200:
        # 安全处理文本，用于文件名
        safe_text = safe_filename(text_base_name)
        audio_file_name = f"{chaName}_{safe_text}_audio.wav"
        audio_file_path = os.path.join(output_dir, audio_file_name)
        with open(audio_file_path, "wb") as audio_file:
            audio_file.write(response.content)
        return audio_file_path
    else:
        print(f"Error: Failed to generate speech for text with status code: {response.status_code}")
        return None

# 流式音频处理函数
def play_audio_stream(text, output_dir, text_base_name, chaName, characterEmotion="default", textLanguage="多语种混合",
                   topK=40, topP=0.9, temperature=0.7,stream="False",save_temp="False"):
    # 构造请求体，使用函数参数
    body = {
        "text": text,
        "cha_name": chaName,
        "text_language": textLanguage,
        "top_k": topK,
        "top_p": topP,
        "temperature": temperature,
        "character_emotion": characterEmotion,
        "stream": stream,
        "save_temp": save_temp
    }

    # 发送POST请求
    response = requests.post(TTS_API_URL, json=body, stream=True)
    # 检查请求是否成功

    global p, streamAudio
    # 打开音频流
    streamAudio = p.open(format=p.get_format_from_width(2),
                         channels=1,
                         rate=32000,
                         output=True)
    # 是不是重复了？
    # response = requests.post(TTS_API_URL, json=body, stream=True)
    if response.status_code == 200:

        save_path = os.path.join(output_dir, f"{chaName}_{text_base_name}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.wav")


        # 检查保存路径是否存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(save_path, "wb") as f:
            # 读取数据块并播放
            for data in response.iter_content(chunk_size=1024):
                f.write(data)
                if (streamAudio is not None) and (not streamAudio.is_stopped()):
                    streamAudio.write(data)

        # 停止和关闭流
        if streamAudio is not None:
            streamAudio.stop_stream()
        return gr.Audio(save_path, type="filepath")
    else:
        gr.Warning(f"请求失败，状态码：{response.status_code}, 返回内容：{response.content}")
        return gr.Audio(None, type="filepath")

    # 处理响应
def stopAudioPlay():
    global streamAudio
    if streamAudio is not None:
        streamAudio.stop_stream()
        streamAudio = None



def extract_chinese_subtitles(ass_file_path):
    with open(ass_file_path, "r", encoding="utf-8") as file:
        content = file.read()
    matches = re.findall(r"Dialogue: [^,]*,[^,]*,[^,]*,chn_sub,[^,]*,[^,]*,[^,]*,[^,]*,,(.+)", content)
    return matches

def read_text_file(text_file_path):
    with open(text_file_path, "r", encoding="utf-8") as file:
        return file.read()

def generate_speech(subtitle_text, character_name, subtitle_base_name, index, output_dir):
    # 修改这里来调整目录结构
    audio_path = text_to_speech(subtitle_text, index, output_dir, subtitle_base_name, chaName=character_name)
    return audio_path






# 定义处理函数
def main_input_text(input_text, character_name):
    if not character_name:
        character_name = "胡桃(测试)"

    # 假设使用当前目录作为输出目录
    output_dir = "AUDIO_FILES/InputText"
    os.makedirs(output_dir, exist_ok=True)

    # 调用 text_to_speech_txt 函数，将输入文本转换为音频
    audio_path = text_to_speech_txt(input_text, output_dir, "input_text", chaName=character_name)
    if audio_path:
        print(f"输入文本已转换为语音并保存到 '{audio_path}'。")
    else:
        print("由于错误，输入文本转换为语音失败。")

    return audio_path

# 流式音频播放的事件处理函数
def handle_stream_request(input_text, character_name):
    if not character_name:
        character_name = "胡桃(测试)"

    # 假设使用当前目录作为输出目录
    output_dir = "AUDIO_FILES"
    os.makedirs(output_dir, exist_ok=True)

    # 调用 play_audio_stream 函数处理音频流
    audio_stream = play_audio_stream(input_text, output_dir, "input_text", chaName=character_name, stream="True")
    if audio_stream:
        print(f"输入文本已转换为语音并保存到 '{audio_stream}'。")
    else:
        print("由于错误，输入文本转换为语音失败。")

    return audio_stream


def main_subtitle(subtitle_file, character_name):
    # 如果 character_name 为空，则设置默认值为 "胡桃(测试)"
    if not character_name:
        character_name = "胡桃(测试)"
    subtitles = extract_chinese_subtitles(subtitle_file)
    subtitle_base_name = os.path.splitext(os.path.basename(subtitle_file.name))[0]

    # 创建目录结构
    AUDIO_FILES_ROOT_DIR = "AUDIO_FILES"
    subtitle_dir = os.path.join(AUDIO_FILES_ROOT_DIR, f"{character_name}_{subtitle_base_name}")
    single_sentences_dir = os.path.join(subtitle_dir, "单句音频")
    os.makedirs(single_sentences_dir, exist_ok=True)

    audio_paths = []
    for index, subtitle in enumerate(subtitles, start=1):
        audio_path = generate_speech(subtitle, character_name, subtitle_base_name, index, single_sentences_dir)
        if audio_path:
            audio_paths.append(audio_path)

    combined_audio = AudioSegment.empty()
    for audio_path in audio_paths:
        audio_segment = AudioSegment.from_wav(audio_path)  # 加载WAV文件
        combined_audio += audio_segment

    combined_audio_path = os.path.join(subtitle_dir, f"{character_name}_{subtitle_base_name}_combined_audio.wav")
    combined_audio.export(combined_audio_path, format="wav")
    print(f"所有字幕已转换为语音并合并到 '{combined_audio_path}'。")

    return combined_audio_path

def main_text(text_file_path, character_name):
    # 如果 character_name 为空，则设置默认值为 "胡桃(测试)"
    if not character_name:
        character_name = "胡桃(测试)"
    text_content = read_text_file(text_file_path)
    text_base_name = os.path.splitext(os.path.basename(text_file_path.name))[0]

    # 创建目录结构
    AUDIO_FILES_ROOT_DIR = "AUDIO_FILES"
    text_dir = os.path.join(AUDIO_FILES_ROOT_DIR, f"{character_name}_{text_base_name}")

    # 确保目录存在
    os.makedirs(text_dir, exist_ok=True)

    # 由于不需要单句音频，直接将整个文本内容转换为语音
    audio_path = text_to_speech_txt(text_content, text_dir, text_base_name, chaName=character_name)
    if audio_path:
        print(f"文本已转换为语音并保存到 '{audio_path}'。")
    else:
        print("由于错误，文本转换为语音失败。")

    return audio_path

with gr.Blocks() as app:
    # 使用 Markdown 组件来设置标题和描述，实现之前想通过构造函数设置的效果
    gr.Markdown("<h1 style='font-size: 24px;'>Subtitle and Text to Speech</h1>")
    gr.Markdown("Convert subtitles and text content to speech and merge into a single audio file.")
    with gr.Row():
        gr.Markdown("---")
    with gr.Row():
        gr.Markdown("<h2 style='font-size: 18px;'>输入文字转语音</h2>")

        # 输入文本和角色选择
    with gr.Row():
        input_text = gr.Textbox(value=default_text, label="输入文本", interactive=True, lines=8)
        character_name_input = gr.Textbox(label="Character Name", placeholder="Enter character name here...")

    # Tabs for 完整音频和流式音频
    with gr.Tabs():
        with gr.Tab(label="请求完整音频"):
            with gr.Row():
                sendRequest = gr.Button("发送请求", variant="primary")
                audioRecieve = gr.Audio(None, label="音频输出", type="filepath", streaming=False)

        with gr.Tab(label="流式音频"):
            with gr.Row():
                sendStreamRequest = gr.Button("发送并开始播放", variant="primary", interactive=True)
                stopStreamButton = gr.Button("停止播放", variant="secondary")
            with gr.Row():
                audioStreamRecieve = gr.Audio(None, label="音频输出", interactive=False,streaming=True)

    # 为"发送请求"按钮绑定事件处理函数，这里假设有对应的函数实现
    sendRequest.click(fn=main_input_text, inputs=[input_text, character_name_input], outputs=audioRecieve)

    # 为"发送并开始播放"按钮绑定事件处理函数，这里假设有对应的函数实现
    sendStreamRequest.click(fn=handle_stream_request, inputs=[input_text, character_name_input],
                            outputs=audioStreamRecieve)

    # 为"停止播放"按钮绑定事件处理函数，这里假设有对应的函数实现
    stopStreamButton.click(fn=stopAudioPlay, inputs=[], outputs=[])

    with gr.Row():
        gr.Markdown("---")
    with gr.Row():
        gr.Markdown("<h2 style='font-size: 18px;'>上传字幕转语音</h2>")

    with gr.Row():
        subtitle_file = gr.File(label="Upload your subtitle file")
        character_name_subtitle = gr.Textbox(label="Character Name (Subtitle)", placeholder="Enter character name here...")
    with gr.Row():
        submit_button_subtitle = gr.Button("Convert Subtitle to Speech", variant="primary")
        audio_output_subtitle = gr.Audio(None, label="Audio Output (Subtitle)", type="filepath", streaming=True)

    submit_button_subtitle.click(fn=main_subtitle, inputs=[subtitle_file, character_name_subtitle], outputs=audio_output_subtitle)

    with gr.Row():
        gr.Markdown("---")
    with gr.Row():
        gr.Markdown("<h2 style='font-size: 18px;'>上传文本文件转语音</h2>")

    with gr.Row():
        text_file_path = gr.File(label="Upload your text file")
        character_name_text = gr.Textbox(label="Character Name (Text)", placeholder="Enter character name here...")
    with gr.Row():
        submit_button_text = gr.Button("Convert Text to Speech", variant="primary")
        audio_output_text = gr.Audio(None, label="Audio Output (Text)", type="filepath", streaming=True)

    submit_button_text.click(fn=main_text, inputs=[text_file_path, character_name_text], outputs=audio_output_text)

app.launch(server_port=7861, show_error=True)
