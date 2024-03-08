import gradio as gr
import requests
import re
import os
from pydub import AudioSegment
import pyaudio
from datetime import datetime

default_text = "那年五月至第二年的年初，我住在一条狭长山谷入口附近的山顶上。夏天，山谷深处雨一阵阵下个不停，而山谷外面大体是白云蓝天——那是海上有西南风吹来的缘故。"
# 后端服务的地址
TTS_API_URL = "http://192.168.50.63:5000/tts"

global p,streamAudio
p = pyaudio.PyAudio()
streamAudio = None

# 文件名安全处理函数，用于移除或替换文件名中不允许的字符
def safe_filename(text, max_length=50):
    # 移除或替换文件名中不允许的字符
    safe_text = re.sub(r'[\\/*?:"<>|]', "", text)
    # 限制文件名长度，防止过长
    if len(safe_text) > max_length:
        safe_text = safe_text[:max_length - 3] + "..."
    return safe_text

# TTS API用于发送请求并接收返回的音频文件
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



# 完整音频播放的事件处理函数
def handle_request(input_text, character_name):
    if not character_name:
        character_name = "胡桃(测试)"

    # 假设使用当前目录作为输出目录
    output_dir = "AUDIO_FILES"
    os.makedirs(output_dir, exist_ok=True)

    # 调用 text_to_speech_txt 函数，将输入文本转换为音频
    audio_path = text_to_speech_txt(input_text, output_dir, "input_text", chaName=character_name, stream="False")
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
    sendRequest.click(fn=handle_request, inputs=[input_text, character_name_input], outputs=audioRecieve)

    # 为"发送并开始播放"按钮绑定事件处理函数，这里假设有对应的函数实现
    sendStreamRequest.click(fn=handle_stream_request, inputs=[input_text, character_name_input],
                           outputs=audioStreamRecieve)

    # 为"停止播放"按钮绑定事件处理函数，这里假设有对应的函数实现
    stopStreamButton.click(fn=stopAudioPlay, inputs=[], outputs=[])

app.launch(server_port=7861, show_error=True)