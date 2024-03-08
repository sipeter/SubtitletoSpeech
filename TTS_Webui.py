from datetime import datetime
import gradio as gr
import json, os
import requests
import numpy as np
from string import Template
import pyaudio

def load_character_emotions(character_name, characters_and_emotions):
    emotion_options = ["default"]
    emotion_options = characters_and_emotions.get(character_name, ["default"])

    return gr.Dropdown(emotion_options, value="default")

global p,streamAudio
p = pyaudio.PyAudio()
streamAudio = None

def send_request(
    endpoint,
    endpoint_data,
    text,
    cha_name,
    text_language,
    top_k,
    top_p,
    temperature,
    character_emotion,
    stream="False",
):
    
    urlencoded_text = requests.utils.quote(text)

    # 使用Template填充变量
    endpoint_template = Template(endpoint)
    final_endpoint = endpoint_template.substitute(
        chaName=cha_name,
        speakText=urlencoded_text,
        textLanguage=text_language,
        topK=top_k,
        topP=top_p,
        temperature=temperature,
        characterEmotion=character_emotion,
        stream=stream,
    )

    endpoint_data_template = Template(endpoint_data)
    filled_json_str = endpoint_data_template.substitute(
        chaName=cha_name,
        speakText=urlencoded_text,
        textLanguage=text_language,
        topK=top_k,
        topP=top_p,
        temperature=temperature,
        characterEmotion=character_emotion,
        stream=stream,
    )
    # 解析填充后的JSON字符串
    request_data = json.loads(filled_json_str)
    body = request_data["body"]
    if stream.lower() == "false":
        print(f"发送请求到{final_endpoint}")
        # 发送POST请求
        response = requests.post(final_endpoint, json=body)
        # 检查请求是否成功
        if response.status_code == 200:
            # 生成保存路径
            save_path = (
                f"tmp_audio/{cha_name}{datetime.now().strftime('%Y%m%d%H%M%S%f')}.wav"
            )

            # 检查保存路径是否存在
            if not os.path.exists("tmp_audio"):
                os.makedirs("tmp_audio")

            # 保存音频文件到本地
            with open(save_path, "wb") as f:
                f.write(response.content)

            # 返回给gradio
            return gr.Audio(save_path, type="filepath")
        else:
            gr.Warning(f"请求失败，状态码：{response.status_code}, 返回内容：{response.content}")
            return gr.Audio(None, type="filepath")
    else:
    # 发送POST请求
        response = requests.post(final_endpoint, json=body, stream=True)
        # 检查请求是否成功

        global p,streamAudio
        # 打开音频流
        streamAudio = p.open(format=p.get_format_from_width(2),
                        channels=1,
                        rate=32000,
                        output=True)

        
        response = requests.post(final_endpoint, json=body, stream=True)
        if response.status_code == 200:
            save_path = (
                f"tmp_audio/{cha_name}{datetime.now().strftime('%Y%m%d%H%M%S%f')}.wav"
            )

            # 检查保存路径是否存在
            if not os.path.exists("tmp_audio"):
                os.makedirs("tmp_audio")
            with open(save_path, "wb") as f:    
            # 读取数据块并播放
                for data in response.iter_content(chunk_size=1024):
                    f.write(data)
                    if (streamAudio is not None) and (not streamAudio.is_stopped()) :
                        streamAudio.write(data)

            # 停止和关闭流
            if streamAudio is not None:
                streamAudio.stop_stream()
            return gr.Audio(save_path, type="filepath")
        else:
            gr.Warning(f"请求失败，状态码：{response.status_code}, 返回内容：{response.content}")
            return gr.Audio(None, type="filepath")


def stopAudioPlay():
    global streamAudio
    if streamAudio is not None:
        streamAudio.stop_stream()
        streamAudio = None

def get_characters_and_emotions(character_list_url):
    try:
        response = requests.get(character_list_url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"请求失败，状态码：{response.status_code}")
    except:
        raise Exception("请求失败，请检查URL是否正确")


def change_character_list(
    character_list_url, cha_name="", auto_emotion=False, character_emotion="default"
):

    characters_and_emotions = {}

    try:
        characters_and_emotions = get_characters_and_emotions(character_list_url)
        character_names = [i for i in characters_and_emotions]
        if len(character_names) != 0:
            if cha_name in character_names:
                character_name_value = cha_name
            else:
                character_name_value = character_names[0]
        else:
            character_name_value = ""
        emotions = characters_and_emotions.get(character_name_value, ["default"])
        emotion_value = character_emotion
        if auto_emotion == False and emotion_value not in emotions:
            emotion_value = "default"
    except:
        character_names = []
        character_name_value = ""
        emotions = ["default"]
        emotion_value = "default"
        characters_and_emotions = {}
    if auto_emotion:
        return (
            gr.Dropdown(character_names, value=character_name_value, label="选择角色"),
            gr.Checkbox(auto_emotion, label="是否自动匹配情感"),
            gr.Dropdown(["auto"], value="auto", label="情感列表", interactive=False),
            characters_and_emotions,
        )
    return (
        gr.Dropdown(character_names, value=character_name_value, label="选择角色"),
        gr.Checkbox(auto_emotion, label="是否自动匹配情感"),
        gr.Dropdown(emotions, value=emotion_value, label="情感列表", interactive=True),
        characters_and_emotions,
    )


def change_endpoint(url):
    url = url.strip()
    return gr.Textbox(f"{url}/tts"), gr.Textbox(f"{url}/character_list")


tts_port = 5000

# 取得模型文件夹路径
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        _config = json.load(f)
        tts_port = _config.get("tts_port", 5000)
        is_share = _config.get("is_share", "false").lower() == "true"

default_request_url = f"http://127.0.0.1:{tts_port}"
default_character_info_url = f"{default_request_url}/character_list"
default_endpoint = f"{default_request_url}/tts"
default_endpoint_data = """{
    "method": "POST",
    "body": {
        "cha_name": "${chaName}",
        "character_emotion": "${characterEmotion}",
        "text": "${speakText}",
        "text_language": "${textLanguage}",
        "top_k": ${topK},
        "top_p": ${topP},
        "temperature": ${temperature},
        "stream": "${stream}",
        "save_temp": "False"
    }
}"""
default_text = (
    "那年五月至第二年的年初，我住在一条狭长山谷入口附近的山顶上。夏天，山谷深处雨一阵阵下个不停，"
    "而山谷外面大体是白云蓝天——那是海上有西南风吹来的缘故。风带来的湿乎乎的云进入山谷，"
    "顺着山坡往上爬时就让雨降了下来。房子正好建在其分界线那里，所以时不时出现这一情形："
    "房子正面一片明朗，而后院却大雨如注。起初觉得相当不可思议，但不久习惯之后，反倒以为理所当然。"
    "周围山上低垂着时断时续的云。每当有风吹来，那样的云絮便像从前世入此间的魂灵一样为寻觅失去的记忆而在山间飘忽不定。"
    "看上去宛如细雪的白亮亮的雨，有时也悄无声息地随风起舞。差不多总有风吹来，没有空调也能大体快意地度过夏天。"
)

with gr.Blocks() as app:

    gr.HTML("""<p>API 调用测试代码，使用前确认：</p>
            <p>API 服务开启</p>
            <p>角色设置完成</p>""")
    with gr.Row():
        text = gr.Textbox(value=default_text, label="输入文本",interactive=True,lines=8)
    with gr.Row():
        with gr.Column(scale=2):
            text_language = gr.Dropdown(["多语种混合", "中文", "英文","日文","中英混合","日英混合"], value="多语种混合", label="文本语言")

            cha_name, auto_emotion_checkbox , character_emotion, characters_and_emotions_ = change_character_list(default_character_info_url)
            characters_and_emotions = gr.State(characters_and_emotions_)
            scan_character_list = gr.Button("重新扫描人物列表",variant="secondary")
        with gr.Column(scale=1):    
            top_k = gr.Slider(minimum=1, maximum=30, value=6, label="Top K",step=1)
            top_p = gr.Slider(minimum=0, maximum=1, value=0.8, label="Top P")
            temperature = gr.Slider(minimum=0, maximum=1, value=0.8, label="Temperature")
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.Tab(label="网址设置"):
                    request_url_input = gr.Textbox(value=default_request_url, label="请求网址",interactive=True)
                    endpoint = gr.Textbox(value=default_endpoint, label="Endpoint",interactive=False)
                    character_list_url = gr.Textbox(value=default_character_info_url, label="人物情感列表网址",interactive=False)
                    request_url_input.blur(change_endpoint, inputs=[request_url_input],outputs=[endpoint,character_list_url])
                with gr.Tab(label="json设置（一般不动）"):
                    endpoint_data = gr.Textbox(value=default_endpoint_data, label="发送json格式",lines=10)
    with gr.Tabs():
        with gr.Tab(label="请求完整音频"):
            with gr.Row():
                sendRequest = gr.Button("发送请求",variant="primary")
                audioRecieve = gr.Audio(None, label="音频输出",type="filepath",streaming=False)
        with gr.Tab(label="流式音频"):
            with gr.Row():
                sendStreamRequest = gr.Button("发送并开始播放",variant="primary",interactive=True)
                stopStreamButton = gr.Button("停止播放",variant="secondary")
            with gr.Row():
                audioStreamRecieve = gr.Audio(None, label="音频输出",interactive=False)
    sendRequest.click(lambda: gr.update(interactive=False), None, [sendRequest]).then(
        send_request,
        inputs=[
            endpoint,
            endpoint_data,
            text,
            cha_name,
            text_language,
            top_k,
            top_p,
            temperature,
            character_emotion,
            gr.State("False"),
        ],
        outputs=[audioRecieve],
    ).then(lambda: gr.update(interactive=True), None, [sendRequest])
    sendStreamRequest.click(
        lambda: gr.update(interactive=False), None, [sendStreamRequest]
    ).then(
        send_request,
        inputs=[
            endpoint,
            endpoint_data,
            text,
            cha_name,
            text_language,
            top_k,
            top_p,
            temperature,
            character_emotion,
            gr.State("True"),
        ],
        outputs=[audioStreamRecieve],
    ).then(
        lambda: gr.update(interactive=True), None, [sendStreamRequest]
    )
    stopStreamButton.click(stopAudioPlay, inputs=[])
    cha_name.change(
        load_character_emotions,
        inputs=[cha_name, characters_and_emotions],
        outputs=[character_emotion],
    )
    character_list_url.change(
        change_character_list,
        inputs=[character_list_url, cha_name, auto_emotion_checkbox, character_emotion],
        outputs=[
            cha_name,
            auto_emotion_checkbox,
            character_emotion,
            characters_and_emotions,
        ],
    )
    scan_character_list.click(
        change_character_list,
        inputs=[character_list_url, cha_name, auto_emotion_checkbox, character_emotion],
        outputs=[
            cha_name,
            auto_emotion_checkbox,
            character_emotion,
            characters_and_emotions,
        ],
    )
    auto_emotion_checkbox.input(
        change_character_list,
        inputs=[character_list_url, cha_name, auto_emotion_checkbox, character_emotion],
        outputs=[
            cha_name,
            auto_emotion_checkbox,
            character_emotion,
            characters_and_emotions,
        ],
    )


app.launch(server_port=9867, show_error=True, share=is_share)
