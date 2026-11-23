# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""48 synthetic CT evidence questions, authored by the assistant.

These are initial annotations for source-grounded offline experiments, not
clinician-validated answers. Split assignment is by scenario family before any
retrieval or generation run. Original v1 cases/holdout are never read here.
"""

# 设置USP：字符串 'uspstf-screening-2021::'。
USP = "uspstf-screening-2021::"
# 设置NCI：字符串 'nci-lung-screening-pdq-hp::'。
NCI = "nci-lung-screening-pdq-hp::"
# 设置OV：字符串 'nci-screening-overview-pdq-hp::'。
OV = "nci-screening-overview-pdq-hp::"
# 设置INC：字符串 'acr-incidental-2023::'。
INC = "acr-incidental-2023::"
# 设置LR：字符串 'acr-lungrads-2022::p2::note'。
LR = "acr-lungrads-2022::p2::note"

# These labels were prepared against these snapshots, not future website content.
# 固定合成标注所依据的来源指纹，源文件变化时必须重新复核标注。
SOURCE_SNAPSHOT_SHA256 = {
    # 写入字段 acr-lungrads-scope（ACR筛查框架入口页快照的固定SHA-256）。
    "acr-lungrads-scope": "b5ca0d54a291f7646723c056d329aca412f4ac08d149d7c96b9632af3fdd3328",
    # 写入字段 acr-lungrads-2022（Lung-RADS v2022 PDF快照的固定SHA-256）。
    "acr-lungrads-2022": "3eca605a00ab4bf8985ecffd3bd614dcee5980578e309cd5599246394cea61bd",
    # 写入字段 acr-incidental-2023（ACR偶发结节来源快照的固定SHA-256）。
    "acr-incidental-2023": "6491745ffe05c22c500054949bb209744369de8e873e7bbeb81bea46f5b5f58d",
    # 写入字段 uspstf-screening-2021（USPSTF筛查声明快照的固定SHA-256）。
    "uspstf-screening-2021": "d81f89c6a00e3f895cedc5acbbca77446217c04ba41b383756a72d40ae289fd6",
    # 写入字段 nci-lung-screening-pdq-hp（NCI肺癌筛查专业版快照的固定SHA-256）。
    "nci-lung-screening-pdq-hp": "64f395b7f6dcfd2231467a6ffcab084de53c48e9976a2307930d1ea17c17eff4",
    # 写入字段 nci-screening-overview-pdq-hp（NCI筛查总览专业版快照的固定SHA-256）。
    "nci-screening-overview-pdq-hp": "742ac20e58e4578135203be3cd9da698dda80dbeabfea7888da2fdf2139ef861",
# 结束上方的字典或集合。
}


# 定义 family：创建一个合成场景家族，固定划分、任务、证据组和禁止扩大结论的规则。
def family(name, split, task, groups, examples, forbidden=None):
    # 返回字典，保存场景家族名称、开发集或留出集的固定划分、这道题需要验证的任务、每项证据需求允许命中的替代证据组、同一场景家族内的合成题等信息，结束本次函数调用。
    return {"family": name, "split": split, "task": task, "evidence_groups": groups,
            # 写入字段 examples（同一场景家族内的合成题）；字段 forbidden（禁止无依据扩大回答的规则）。
            "examples": examples, "forbidden": forbidden or []}


# 定义 example：创建一条合成报告题，保存问题、AI 初标预期行为与缺失条件。
def example(report, question, expected, missing=None, evidence_groups=None):
    # 设置value：字典，保存作为查询输入的合成报告、作为查询输入的问题、AI 初标的参考行为，尚非临床复核结论、当前任务确实缺少、需要追问的条件。
    value = {"report": report, "question": question, "expected_behavior": expected,
             # 写入字段 required_missing_fields（当前任务确实缺少、需要追问的条件）。
             "required_missing_fields": missing or []}
    # 当 evidence_groups is not None 成立时，执行下面的分支。
    if evidence_groups is not None:
        # 设置value['evidence_groups']：evidence_groups。
        value["evidence_groups"] = evidence_groups
    # 返回value，结束本次函数调用。
    return value


# 按场景家族列出合成题及预先划分；不是已被医生验证的临床答案。
FAMILIES = [
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务。
    family("screening_framework", "dev", "guideline_selection",
           # 设置需求组及可替代证据 ID；开始本家族的合成题列表。
           [[USP + "b0020", "acr-lungrads-scope::b0001"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("Baseline low-dose chest CT within an organized lung cancer screening program. A 61-year-old adult has a single solid right-upper-lobe nodule; size is not stated.",
                # 记录这条合成题的问题输入。
                "Which reporting framework should I consult, and what report fact determines that choice?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "选择 Lung-RADS；关键是报告明确为肺癌筛查 CT。当前只问框架选择，结节尺寸缺失不阻碍这一层判断。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("Annual screening LDCT. A 67-year-old adult has two left-lung nodules. Smoking exposure is not included in this imaging report.",
                # 记录这条合成题的问题输入。
                "For interpreting this completed screening examination, which framework is relevant? Is smoking exposure a prerequisite for naming it?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "Lung-RADS 与已明确的筛查影像解释场景匹配。将筛查资格核对与已完成检查的报告框架选择分开；不将补吸烟史作为命名框架的必要条件。"),
    # 记录禁止无依据扩展的回答内容。
    ], ["不能依据筛查资格声明直接给本例结节分类", "不能把结节大小设为仅选择框架时的必答前提"]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务。
    family("missing_examination_purpose", "dev", "clarification",
           # 设置需求组及可替代证据 ID；开始本家族的合成题列表。
           [[USP + "b0020"], [INC + "b0021"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("Chest CT: a 63-year-old adult with a single 7 mm solid pulmonary nodule. The indication is absent. No known cancer or immunosuppression is recorded.",
                # 记录这条合成题的问题输入。
                "Which guideline pathway applies to this nodule, and what must be clarified first?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论；记录当前问题需要追问的缺失条件字段。
                "先追问检查是否属于肺癌筛查项目，还是因其他原因检查时偶发发现。现有材料分别描述筛查与偶发场景，不应擅自补出检查目的。", ["examination_purpose"]),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A 58-year-old adult has a 9 mm solid nodule on CT. The referral and the screening-program status are unavailable.",
                # 记录这条合成题的问题输入。
                "Can you select a screening versus incidental-nodule framework from this report alone?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论；记录当前问题需要追问的缺失条件字段。
                "不能唯一分流；具体询问检查目的／筛查项目身份，保留两类来源的适用前提。无需先追问与该层分流无关的结节边缘。", ["examination_purpose"]),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务。
    family("screening_age_condition", "dev", "eligibility_check",
           # 设置需求组及可替代证据 ID；开始本家族的合成题列表。
           [[USP + "b0001", USP + "b0007"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("An asymptomatic 49-year-old adult currently smokes, with 25 pack-years, good functional status and willingness to consider curative lung surgery.",
                # 记录这条合成题的问题输入。
                "Does this person meet the age and smoking conditions in the 2021 USPSTF lung screening statement?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "吸烟暴露满足所引条款，但 49 岁低于该声明 50 岁的下限。只判断这一声明的适用条件，不据此作所有机构或诊断性 CT 的结论。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("An asymptomatic 51-year-old adult currently smokes and has 25 pack-years. No limiting comorbidity or unwillingness for curative surgery is reported.",
                # 记录这条合成题的问题输入。
                "Are the stated age and smoking conditions consistent with the 2021 USPSTF recommendation?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "已知年龄与当前吸烟暴露符合所引声明的条件；保留共同决策及整体适宜性边界，不把资格判断当成结节类别。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务。
    family("screening_exposure_condition", "dev", "eligibility_check",
           # 设置需求组及可替代证据 ID；开始本家族的合成题列表。
           [[USP + "b0001", USP + "b0007"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A healthy asymptomatic 64-year-old current smoker reports 10 pack-years.",
                # 记录这条合成题的问题输入。
                "Does the stated smoking exposure meet the 2021 USPSTF LDCT screening threshold?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "10 包年未达到所引 20 包年阈值；年龄满足不代表整个条件满足，不扩大到其他检查指征。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A healthy asymptomatic 64-year-old current smoker reports 22 pack-years and would consider curative lung surgery.",
                # 记录这条合成题的问题输入。
                "Do age and exposure meet the stated 2021 USPSTF conditions?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "年龄与已知吸烟条件符合所引声明；这是资格条件核对，不是 Lung-RADS 分类或癌症诊断。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务。
    family("screening_quit_duration", "dev", "eligibility_check",
           # 设置需求组及可替代证据 ID；开始本家族的合成题列表。
           [[USP + "b0001", USP + "b0007"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("An asymptomatic 69-year-old former smoker has 35 pack-years and stopped smoking 16 years ago.",
                # 记录这条合成题的问题输入。
                "How does time since quitting affect applicability of the 2021 USPSTF statement?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "16 年已超过所引戒烟时间范围；说明该声明的条件，不把其他诊断性检查一并否定。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("An asymptomatic 69-year-old former smoker has 35 pack-years and stopped smoking 10 years ago, without stated limiting comorbidity.",
                # 记录这条合成题的问题输入。
                "Do the recorded age, exposure and quit duration meet the statement's stated conditions?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "这些已知条件符合所引年龄、暴露及戒烟时间条件；仍区分条件符合和个体共同决策。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务。
    family("missing_screening_eligibility_facts", "dev", "clarification",
           # 设置需求组及可替代证据 ID；开始本家族的合成题列表。
           [[USP + "b0001", USP + "b0007"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("An asymptomatic 62-year-old adult currently smokes. Cumulative smoking exposure is not recorded.",
                # 记录这条合成题的问题输入。
                "Can eligibility under the 2021 USPSTF statement be confirmed, and what specific fact is missing?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论；记录当前问题需要追问的缺失条件字段。
                "不能确认暴露条件；具体补充累计包年，必要时由每天吸烟量和年数计算。当前问题无需结节尺寸。", ["pack_years"]),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("An asymptomatic 72-year-old former smoker reports 30 pack-years. The date of quitting is absent.",
                # 记录这条合成题的问题输入。
                "Which missing condition prevents completion of the USPSTF eligibility check?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论；记录当前问题需要追问的缺失条件字段。
                "需要戒烟距今年数；年龄和包年已知，不把这些重复列成缺项。", ["years_since_quitting"]),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务；设置需求组及可替代证据 ID；开始本家族的合成题列表。
    family("prior_comparison_state", "dev", "applicability_check", [[LR + "9"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("Screening LDCT shows a pulmonary nodule. Prior screening or diagnostic chest CT examinations are being located for comparison and have not yet arrived.",
                # 记录这条合成题的问题输入。
                "What does Lung-RADS note 9 say about the temporary assessment while prior examinations are being sought?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "明确引用注释 9 的正在调取状态及暂时性；对比影像可用后重新赋类。不能把这一条改成所有存在既往 CT 的病例都为 0 类。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("Screening LDCT has an accessible prior diagnostic chest CT; the radiologist has completed the comparison. Nodule measurements are omitted from this summary.",
                # 记录这条合成题的问题输入。
                "Does the mere existence of prior CT justify applying the temporary state described in note 9?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "不满足正在等待既往检查这一触发状态；不能仅凭有既往 CT 套用该暂时状态。也不能据此直接推出最终类别。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务；设置需求组及可替代证据 ID；开始本家族的合成题列表。
    family("diameter_measurement", "dev", "measurement_rule", [[LR + "4"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("Screening CT: a nodule has a long-axis diameter of 6.8 mm and a short-axis diameter of 5.6 mm measured in one plane.",
                # 记录这条合成题的问题输入。
                "According to Lung-RADS note 4, how is mean diameter reported, and what is it for these measurements?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "均值由长短轴计算并以毫米保留一位小数；本例为 6.2 mm。此计算不自动完成结节类别和随访判断。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("Screening CT: measured long and short axes are 7.3 mm and 5.9 mm. The report currently lists only the longest axis.",
                # 记录这条合成题的问题输入。
                "Which measurement rule is relevant, and what mean diameter follows from the supplied values?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "引用注释 4 的均径与精度规则；算得 6.6 mm，不将最长径直接冒充均径。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务；设置需求组及可替代证据 ID；开始本家族的合成题列表。
    family("multiple_nodule_assessment", "dev", "applicability_check", [[LR + "1"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A screening examination has several nodules. The largest is described as benign-appearing, while a smaller nodule is described as more suspicious.",
                # 记录这条合成题的问题输入。
                "Does Lung-RADS note 1 select the examination category by the largest nodule or the most suspicious nodule?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "按最高可疑程度的结节决定检查类别；该条不是单纯按最大尺寸排序，也不根据本题给出具体类别。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A screening report contains one pulmonary nodule and no other lung lesion.",
                # 记录这条合成题的问题输入。
                "Does note 1 establish that this report contains multiple nodules or specify a follow-up interval?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "不能凭通用检查赋类原则新增多发事实或推导随访间隔；报告仍为单发，具体分类需相应条款。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务。
    family("screen_result_vs_diagnosis", "dev", "evidence_interpretation",
           # 设置需求组及可替代证据 ID；开始本家族的合成题列表。
           [[LR + "3"], [OV + "b0010"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("An LDCT screening report is labelled Lung-RADS category 1. A patient asks whether this guarantees absence of lung cancer.",
                # 记录这条合成题的问题输入。
                "What do the source definitions support about a negative screening result versus a definitive diagnosis?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "注释 3 将 1／2 类定义为阴性筛查，同时明确阴性不等于个体一定没有肺癌；区分筛查结果与诊断。", evidence_groups=[[LR + "3"]]),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("An LDCT screening result is labelled Lung-RADS category 4. No pathology is available.",
                # 记录这条合成题的问题输入。
                "Does a positive screening label alone establish a cancer diagnosis?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "3／4 类属于阳性筛查定义；结合 NCI 对筛查阳性需进一步评价的说明，不能把阳性标签直接当病理确诊。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务；设置需求组及可替代证据 ID；开始本家族的合成题列表。
    family("diagnosis_changes_exam_purpose", "dev", "applicability_check", [[LR + "16"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("Lung cancer has already been diagnosed. PET/CT is requested specifically for cancer staging.",
                # 记录这条合成题的问题输入。
                "Under Lung-RADS note 16, is this subsequent examination still lung cancer screening?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "确诊后为分期而做的后续检查不再属于筛查；保留确诊及分期目的两个事实，不套用筛查逻辑代替分期。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("An asymptomatic participant has a screen-detected nodule but no established cancer diagnosis. A colleague says that any nodule automatically makes the examination cancer staging.",
                # 记录这条合成题的问题输入。
                "Does note 16 support that statement for the facts supplied?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "注释 16 的前提是已经诊断肺癌；结节发现本身未满足此前提，不能从该条推出已经进入确诊后分期场景。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务；设置需求组及可替代证据 ID；开始本家族的合成题列表。
    family("nci_document_type", "dev", "source_type_check", [[NCI + "b0070"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A clinician retrieves the NCI Lung Cancer Screening professional PDQ summary while reviewing a screening CT report.",
                # 记录这条合成题的问题输入。
                "Should this document be labelled a formal clinical guideline or an evidence summary?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "标记为证据综述；其 Purpose of This Summary 明确不提供正式临床指南或医疗决策推荐。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A draft answer says that every study description in the NCI lung screening PDQ is an NCI clinical recommendation.",
                # 记录这条合成题的问题输入。
                "Is that characterization supported by the document's stated purpose?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "不支持；文献证据综述不能自动升级为机构正式推荐，说明该来源独立综述的性质。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务。
    family("trial_population_vs_recommendation", "dev", "cross_source_check",
           # 设置需求组及可替代证据 ID；开始本家族的合成题列表。
           [[NCI + "b0003"], [USP + "b0001", USP + "b0007"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("An asymptomatic 52-year-old current smoker has 22 pack-years. A colleague cites a trial enrolling people aged 55 to 74 with 30+ pack-years to reject the person under the 2021 USPSTF statement.",
                # 记录这条合成题的问题输入。
                "How should the trial population and the recommendation population be distinguished?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "分别引用 NCI 转述的试验纳入条件与 USPSTF 2021 推荐人群；不能用旧试验的 55 岁／30 包年条件替代该声明的 50 岁／20 包年条件。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A clinician compares the original trial population described in NCI PDQ with the 2021 USPSTF eligibility statement and notices different age and smoking thresholds.",
                # 记录这条合成题的问题输入。
                "Does that difference alone demonstrate conflicting recommendations from two guideline bodies?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "不直接构成两个指南推荐冲突；一项是试验人群描述，一项是推荐声明。保留各自证据类型、条件与适用任务。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务。
    family("screening_harms_and_decision", "dev", "evidence_interpretation",
           # 设置需求组及可替代证据 ID；开始本家族的合成题列表。
           [[USP + "b0018"], [OV + "b0004"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A person considering screening asks whether an abnormal result that later proves noncancerous is the same as detecting a cancer that would never become clinically apparent.",
                # 记录这条合成题的问题输入。
                "How do the sources distinguish false-positive results and overdiagnosis for shared decision making?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "区分假阳性与过度诊断，帮助共同决策；不对这个人给出已发生过度诊断的结论。", evidence_groups=[[OV + "b0004"]]),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A screening information sheet mentions only earlier detection and omits false positives, invasive follow-up, overdiagnosis and radiation exposure.",
                # 记录这条合成题的问题输入。
                "Which evidence-supported issues should be included in a balanced screening discussion?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "依据来源讨论筛查的收益、局限及具体伤害，不承诺零风险，也不把一般风险数字当个体确定结局。", evidence_groups=[[USP + "b0018"]]),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务；设置需求组及可替代证据 ID；开始本家族的合成题列表。
    family("incomplete_thoracic_imaging", "dev", "guideline_variant_selection", [[INC + "b0031"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A 57-year-old adult has an incidental pulmonary nodule at the lung base on abdominal CT, which images only part of the chest.",
                # 记录这条合成题的问题输入。
                "Which ACR incidental pulmonary nodule variant matches this imaging context?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "Variant 4 的不完整胸部 CT 场景匹配；保留成人年龄与腹部 CT 只覆盖部分胸部的条件。此题只选变体。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A 74-year-old adult has an incidental apical pulmonary nodule on neck CT. A dedicated complete chest CT has not been performed.",
                # 记录这条合成题的问题输入。
                "Which ACR variant should be checked for the next-imaging question?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "Variant 4；不能把颈部 CT 上的不完整胸部覆盖当成已完成的完整胸部 CT。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务；设置需求组及可替代证据 ID；开始本家族的合成题列表。
    family("radiograph_versus_ct", "dev", "guideline_variant_selection", [[INC + "b0001"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A 59-year-old adult has an incidental indeterminate pulmonary nodule first seen on a chest radiograph. No chest CT has yet been obtained.",
                # 记录这条合成题的问题输入。
                "Which ACR variant applies to the initial imaging modality in this report?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "Variant 1，前提为成人胸片发现；不能按胸部 CT 尺寸变体选择。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A 66-year-old adult has a possible indeterminate lung nodule on a chest x-ray taken for another reason; no CT diameter is available.",
                # 记录这条合成题的问题输入。
                "Should the initial variant be selected from chest-radiograph context or from an assumed CT nodule size?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "按已知胸片场景选择 Variant 1，不能补出 CT 尺寸。当前变体选择不需先编造结节均径。"),
    # 结束上方的列表或索引。
    ]),
    # Entire following families stay held out; generation does not run a model on them.
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务；设置需求组及可替代证据 ID；开始本家族的合成题列表。
    family("slow_growing_ground_glass", "holdout", "applicability_check", [[LR + "7"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("Serial screening reports describe a pure ground-glass nodule growing over several examinations, without exceeding 1.5 mm in any 12-month interval and without a solid component. Other findings criteria are not supplied.",
                # 记录这条合成题的问题输入。
                "What conditional statement in note 7 is relevant, and what prevents an unconditional category assignment?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "保留纯磨玻璃、跨多次增长、任意 12 个月未达阈值以及尚未满足其他类别条件；注释措辞为 may，不能省掉其他条件或直接给固定管理方案。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A formerly pure ground-glass screening nodule has developed a solid component. Solid-component measurement is absent.",
                # 记录这条合成题的问题输入。
                "Can the slow-growing nonsolid-nodule statement be applied unchanged after that new fact?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "注释 7 明确出现实性成分后转按部分实性结节标准；不沿用无实性成分前提。当前只问该条能否原样套用，无需将具体类别所需测量设成回答本题的必答前提。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务；设置需求组及可替代证据 ID；开始本家族的合成题列表。
    family("slow_growing_solid_nodule", "holdout", "applicability_check", [[LR + "8"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A solid nodule grows across multiple screening CT examinations, although no individual 12-month interval shows more than 1.5 mm increase.",
                # 记录这条合成题的问题输入。
                "Does note 8 allow this longitudinal pattern to be dismissed solely because each annual increase is below the threshold?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "注释 8 将此种跨多次增长模式视为可疑并以 may 描述 4B；不能因单个年度阈值未达就断言良性，也不将 may 改为一律。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A slow-growing part-solid screening nodule has no increased metabolic activity on PET/CT.",
                # 记录这条合成题的问题输入。
                "What limitation of PET/CT does note 8 describe for this pattern?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "慢增长结节可能无代谢活性增高；不能把 PET 阴性当作排除的充分证据。保留个体评价和可行性条件，不自动下治疗命令。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务；设置需求组及可替代证据 ID；开始本家族的合成题列表。
    family("airway_nodule_persistence", "holdout", "applicability_check", [[LR + "11"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A baseline screening CT shows a segmental airway nodule. No three-month follow-up has yet occurred and no secretion-only explanation is recorded.",
                # 记录这条合成题的问题输入。
                "Which airway location and timing distinctions in note 11 matter?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "保留段及更近端、基线与持续存在的区别，并注意分泌物等子条件；不能将持续三个月的升级条件套在尚无随访的病例上。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A segmental airway nodule remains present on the three-month follow-up screening CT.",
                # 记录这条合成题的问题输入。
                "Which specific persistence condition in note 11 should be checked?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "引用 11d 的三个月持续存在条件及其来源建议，不能泛化成所有气道异常均自动同类；保留临床进一步评价边界。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务；设置需求组及可替代证据 ID；开始本家族的合成题列表。
    family("cyst_wall_definition", "holdout", "definition_check", [[LR + "12"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("Screening CT describes a unilocular pulmonary cyst with uniform 1 mm wall thickness and no other concerning feature.",
                # 记录这条合成题的问题输入。
                "How does note 12 define this wall pattern, and is it treated as an atypical thick-walled cyst by that definition?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "符合注释 12a 的均匀薄壁小于 2 mm 定义，不能按厚壁定义处理；所引条款说明薄壁囊肿不在 Lung-RADS 分类和管理内。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("Screening CT shows a unilocular cyst with 3 mm nodular wall thickening; the cystic component is dominant.",
                # 记录这条合成题的问题输入。
                "Which cyst definition and stated conditions in note 12 are relevant?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "引用 12b 厚壁／壁结节增厚至少 2 mm、囊性成分占主导的条件；不凭定义 alone 推出具体随访档位。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务；设置需求组及可替代证据 ID；开始本家族的合成题列表。
    family("category_4b_context", "holdout", "missing_context_check", [[LR + "13"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A screening report already assigns category 4B. The clinician has not yet recorded comorbidities or the person's preference.",
                # 记录这条合成题的问题输入。
                "According to note 13, is the label alone enough to choose one fixed management action?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论；记录当前问题需要追问的缺失条件字段。
                "管理依赖临床评价、合并症、患者偏好与恶性风险；类别标签不能替代这些条件。", ["comorbidities", "patient_preference", "malignancy_risk"]),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("Two patients have category 4B screening reports but substantially different comorbidities and preferences.",
                # 记录这条合成题的问题输入。
                "Does note 13 require identical management solely because the labels match?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "不支持只按相同标签给相同处置；应保留注释 13 列出的临床条件，不越过来源替两人制定方案。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务；设置需求组及可替代证据 ID；开始本家族的合成题列表。
    family("category_4x_not_modifier", "holdout", "definition_check", [[LR + "14"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A draft screening report calls X a modifier that can be attached independently of any category 3 or 4 finding.",
                # 记录这条合成题的问题输入。
                "Is that interpretation consistent with note 14?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "注释 14 将 4X 作为独立类别，涉及 3／4 类结节及额外增加怀疑的影像发现；X 不应当修饰符使用。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A screening nodule meets category 3 or 4 findings and has additional spiculation or lymphadenopathy described in the report.",
                # 记录这条合成题的问题输入。
                "Which additional-feature rule should be checked, and what is its scope?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "查注释 14 的额外可疑征象规则；保留原有类别条件与额外发现，不能把该类等同已经确诊肺癌。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务；设置需求组及可替代证据 ID；开始本家族的合成题列表。
    family("s_modifier_known_findings", "holdout", "applicability_check", [[LR + "15"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("Screening CT again shows a clinically significant non-lung-cancer finding that is already known and is undergoing clinical evaluation. No unexpected change is present.",
                # 记录这条合成题的问题输入。
                "Does note 15 require adding an S modifier simply because the known finding is visible again?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "已知且已经或正在临床评价的发现不需要仅因再次显示就加 S；不能把所有显著偶发发现无条件归入同一触发状态。"),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A previously known potentially significant finding unrelated to lung cancer has an unexpected concerning change on a screening CT.",
                # 记录这条合成题的问题输入。
                "Which changed condition in note 15 should be reviewed?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "注释 15b 对已知发现出现意外的可疑变化提出重新使用 S 的情形；保留与肺癌无关的发现及变化条件。"),
    # 结束上方的列表或索引。
    ]),
    # 设置场景家族名称；固定该家族所在的开发／留出划分；记录该家族验证的任务。
    family("survival_and_screening_bias", "holdout", "evidence_interpretation",
           # 设置需求组及可替代证据 ID；开始本家族的合成题列表。
           [[OV + "b0032", OV + "b0033"], [OV + "b0038"]], [
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A screening program reports longer five-year survival after screen detection but provides no randomized mortality comparison.",
                # 记录这条合成题的问题输入。
                "Does improved survival alone establish a mortality benefit from screening, according to the evidence overview?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "不能仅凭生存期改善证明死亡获益；说明提前诊断等偏倚，并区分生存变化与真实筛查获益。", evidence_groups=[[OV + "b0032", OV + "b0038"]]),
        # 记录合成报告文本，后续与问题一起作为输入。
        example("A clinician claims that detecting more early cancers and moving the date of diagnosis earlier proves that people live longer because of the screening test.",
                # 记录这条合成题的问题输入。
                "Which screening biases and stronger outcome evidence should be considered?",
                # 记录 AI 初标的预期行为，不冒充医生复核结论。
                "讨论 lead-time 等偏倚、过度诊断及随机试验死亡终点的价值，不将诊断提前等同实际死亡时间延后。"),
    # 结束上方的列表或索引。
    ]),
# 结束上方的列表或索引。
]
