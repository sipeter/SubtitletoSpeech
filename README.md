# SubtitletoSpeech
这是一个将文本文件转换为语音的项目。

本项目通过调用TTS引擎的API方式，实现了将文本文件转换为语音。

现在支持的文本有：

- ASS字幕文件

- TXT文件

### 运行环境：

python：3.9.13

pytorch：pytorch212+cuda118

本项目基于：

[GPT-soVITS](https://github.com/RVC-Boss/GPT-SoVITS)：用于模型训练

[TTS-for-GPT-soVITS](https://github.com/X-T-E-R/TTS-for-GPT-soVITS)：用于提供API支持

使用方法：

1. 准备GPT-soVITS模型，并导入TTS-for-GPT-soVITS；
2. 启动TTS-for-GPT-soVITS 的API服务；
3. 本机本机环境修改IP地址和端口；
4. 运行SubtitletoSpeech.py。





**TODO:**

  - 通过配置文件选择api接口；
  - 增加直接输入文字生成语音；
  - 支持流式输出

