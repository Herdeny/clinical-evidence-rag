from unittest import result

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

class RewriteResult(BaseModel):
    retrieval_query: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    
def rewrite_query(query, *, llm):
    if not type(query) == str or not query.strip(): raise ValueError(f"Non-standard query: {query}")
    original_query = query
    
    prompts = ChatPromptTemplate.from_messages([
        ("system", """
        - Your task is to generate a single search query, without answering the question.
        - You may refine the wording and keywords or use equivalent expressions without changing the meaning.
        - Preserve all provided population characteristics, numerical values, units, negations, and examination purposes.
        - Keep unknown conditions unknown. Do not infer or add diagnoses, medications, guideline names, or other missing information.
        - Use the same language as the input.
        - If no rewriting is needed, return the original query unchanged.
         """),
        ("human", "{query}")  
    ])
    
    structed_llm = llm.with_structured_output(
        schema=RewriteResult, # 模型输出的不是自然语言吗 scheme 的作用？ # 规定模型按什么结构返回内容，LangChain 会将这些要求传给模型，再用 Pydantic 解析、校验返回内容
        method="function_calling",
        include_raw=True,
    )
    
    messages = prompts.invoke({"query": query})
    responses = structed_llm.invoke(messages)
    raw_response = responses["raw"]
    schema_response = responses["parsed"]
    
    results = {
        "original_query": original_query,
        "retrieval_query": None,
        "changed": None,
        "reason": None,
        "usage_metadata": raw_response.usage_metadata,
        "response_metadata": raw_response.response_metadata,
        "error": None
    }
    

    if not schema_response or responses["parsing_error"] is not None: 
        results["status"] = "error"
        results["error"] = str(responses["parsing_error"]) if responses["parsing_error"] else "No structured parsing results were obtained"
        return results
    
    retrival_query = schema_response.retrieval_query.strip()
    reason = schema_response.reason.strip()
    if not (retrival_query and reason):
        results["status"] = "error"
        results["error"] = "Retrival_query or reason is blank"
        return results
    
    changed = retrival_query != original_query.strip()
    results["status"] = "ok"
    results["reason"] = schema_response.reason.strip()
    results["retrieval_query"] = retrival_query
    results["changed"] = changed
    
    return results
        
    