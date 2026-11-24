# Cross-Encoder重排任务

任务确定与来源核查：2026-11-24。NFCorpus三种检索开发集已实测，Dense四项均值最高；本步固定Dense Top100候选，只改变候选排序。核心函数由用户编写，助手检查实际文件并验收。当前尚无重排实现或实测成绩，官方test及MIRAGE未运行。

## 参考实现、模型与使用条件

[Sentence Transformers官方两阶段说明](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)及其[固定提交示例](https://github.com/huggingface/sentence-transformers/blob/cddcaee3405a5efde83c1d98f89c6ebd6733dab6/examples/sentence_transformer/applications/retrieve_rerank/retrieve_rerank_simple_wikipedia.ipynb)使用检索候选再交叉编码重排。已查阅该示例，不能将示例输出当成本项目的分数；本项目不复制其Wikipedia数据管线。

本步选择[cross-encoder/ms-marco-MiniLM-L6-v2](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2)，英文、22.7M参数、Apache-2.0，训练来源为MS MARCO Passage Ranking。固定revision=233902d25c440f23af6f7d6e94d2946bac0bee0a；权重model.safetensors约90.9MB，无需下载仓库所有ONNX／其他后端。模型卡及官方API已核查，本地尚无该权重、未初始化模型、未发起下载。它是通用英文相关性模型，医学任务收益须实测，不能宣称医学专用或已微调。

本地sentence-transformers==5.7.0已安装，CrossEncoder构造与predict签名已通过本地检查，不需要为本步升级。这个库与现有LangChain HuggingFaceEmbeddings分别承担重排打分与向量编码，向量部分继续沿用现有接口。见[官方CrossEncoder用法](https://www.sbert.net/docs/cross_encoder/usage/usage.html)。

## 本轮完整工作单元

新建项目根目录rerank_core.py，完成一个可复用函数：

    rerank(query, hits, k, *, reranker, batch_size=16)

本函数只对传入候选打分与排序，不创建模型、下载权重、调用检索器或读取qrels。未来CT、NFCorpus及主库共用此接口；不依赖Notebook。

| 参数 | 内容与原因 |
| --- | --- |
| query | 非空原始问题字符串；不添加BGE向量检索前缀 |
| hits | 现有检索器返回的列表，每条含id、text、score及原有来源定位元数据 |
| k | 正整数，重排后保留数量；超过候选数时返回全部候选 |
| reranker | 已初始化的CrossEncoder对象；由运行入口创建一次并注入 |
| batch_size | 正整数，默认16；控制一次前向的句对数，起步值须在实际设备上核验成本 |

构造与候选同序的(query, hit["text"])句对列表，对整个列表调用一次reranker.predict，参数batch_size=batch_size、show_progress_bar=False、convert_to_numpy=True。一次调用由库内部按batch处理，不是把所有100对同时塞进显存，也不要逐条调用100次。

用numpy.asarray整理返回值，要求一维、长度等于候选数、全部有限。每个输出对应同位置输入句对。复制每个候选字典，把原score保存为float类型retrieval_score，把模型相关性分数保存为float类型score，保留id、text、source_id、locator等字段。按(-score, id)排序后取前k条，不原地改hits。

模型输出使用原始logits，允许负数和大于1，不是概率；不做归一化或强制裁剪。原Dense分数与重排分数语义不同，不相加。只在后续明确设计消融时才引入混合权重。

输入检查集中在函数入口：query有效；k与batch_size为非bool正整数；hits中id为非空且唯一的字符串、text为非空字符串、原score可转有限float。输入候选有效但为空时返回[]，不调用predict。模型输出长度错误、维度错误或NaN／Inf时明确抛ValueError，不丢候选掩盖失败。真正的模型运行异常向上传递，不吞掉后继续给出答案。

## 所需库与API

本函数只需numpy与Python内置功能，不必在模块顶层导入CrossEncoder或初始化GPU。numpy.asarray接收模型返回值；.ndim／.shape检查结构，numpy.isfinite(...).all()检查数值。dict.copy()复制候选字典，本函数只改顶层分数字段；zip对应候选与分数，sorted(..., key=...)指定排序，列表切片保留前k条。字典复制不会递归复制嵌套对象，因此不要修改locator等嵌套元数据。

模型类在后续运行入口使用sentence_transformers.CrossEncoder。届时固定模型与revision、device="cuda"、max_length=512、activation_fn=torch.nn.Identity()，下载完成后启用local_files_only=True与进程级离线模式。max_length是query与候选联合输入的token预算，包含特殊token，超过预算由模型分词器截断；原始完整正文继续保留。现在先完成并验收纯函数，不提前粘贴缺少权重的真实模型初始化。

## 函数验收

用一个仅提供predict方法的假打分器，无需模型权重或GPU。三个候选按A、B、C输入，原检索分数任意且保留；假输出为[0.2,0.8,0.8]，k=3时输出B、C、A，k=2时只返回B、C。同分按ID升序，不沿用偶然的输入顺序。

检查predict恰好调用一次，收到原query与对应完整text、指定batch参数；输入hits不变，来源定位字段保留，retrieval_score等于原分数，score为新的float。空候选不调用模型，k超过条数不补候选，负logit正常保留，重复ID、非正k、错误长度／维度和非有限分数被拒绝。用户保存后助手重读当前代码，并提供必要的独立测试；不代写核心函数。

## 函数通过后的实验

在已有公开基准入口增加dense_rerank方法，模型只加载一次，Dense Top100→重排全部100→返回100。保存辅助与配置支持由助手先补齐，再交用户入口接线；不能调用尚未实现的辅助。保留旧三方法及原始产物，记录重排模型版本、句对长度、batch、候选数与计时。

先用相同324条dev原query比较nDCG@10、Recall@10和延迟；最终Top100的候选集合与Dense相同，因此Recall@100应完全相同。324×100=32,400个推理句对，不是新增32,400道题，也不是训练样本。查询编码及向量缓存继续复用；交叉编码需要联合处理query与正文，不能用已有文档向量代替。

真实模型下载、预检和开发集运行稍后由用户在可见终端执行，当前不启动。通过、归档、提交并同步GitHub后继续下一项。开发集方法固定再运行官方test；本步不扩充语料、不调整RRF、不宣称Agent或医学适用性核验已完成。
