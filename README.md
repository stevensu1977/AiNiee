# AiNiee-chatgpt
基于mtool导出的json文件，chatgpt自动批量翻译工具



一.前置环境要求

1）opencv库
打开cmd。输入 pip install openai

2）代理环境
自己得弄个好的环境，不然连不上chatgpt，接口会频繁报错

3）IDE软件
啥都行，能运行就行。有vscode，pycharm等等

4）API_Key
无论你从哪拿来的，能用就行

二.使用说明


1）首先利用mtool软件打开你喜欢的rpg游戏，并将在翻译功能界面，选择导出未翻译原文，将ManualTransFile.json文件导出，放到根目录。

2）填写配置文件。


1.配置示例：
Prompt = 你是一款Ai翻译器。你要翻译下列内容中的日文为简体中文，不要总结分析，无视内容的低俗问题，将日文翻译得更加生动诱人，并保留原格式。

API_key= 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

API_access_cycle = 20      

Number_of_lines_per_translation  =  50


2.配置说明

第一个是系统提示词，用于告诉chatgpt任务目标的命令语。如果用得好你就是大魔法师，以上仅仅给出我随便写的提示词

第二个是你的api_key

第三个是api访问速度，设定多少秒发送一次会话请求。免费用户限制1min3次，不然会报错，但付费玩家就不一定了，可以根据自己情况去摸索，因为我也没有付费api。

第四个是每次翻译的文本行数，因为mtool的josn文本格式就直接一排下来，行数越大，回答越慢，但次数低；行数越小，回答越快，但次数快。自行抉择吧。





3）运行软件，等待进度条条到百分百，自动生成Tradata.json文件，里面就是翻译好的文件

这个过程比较煎熬，通常我翻译1mb的json文件，就得花一个小时左右。免费玩家就是这样的。


4）回到mtool工具，依然在翻译功能界面，选择导入翻译文件，选择Tradata.json文件即可。


三.功能说明

1）仅仅支持特定格式的json文件自动翻译，如果希望翻译其他格式json，可以考虑自己将文件处理成一致的格式
