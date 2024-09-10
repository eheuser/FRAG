import threading

from modules.llm_api import LLMAPI
from modules.rag_query import RAGQuery


def data_query(query_dict, frag, logger):
    res = [ ]
    try:
        pages, meta = frag.query(query_dict)
        for idx, page in enumerate(pages):
            res.append(
                {
                    "meta": meta[idx],
                    "event": page,
                }
            )
    except Exception as e:
        logger.error(f"data_query: raised {e}")
    return res

def stream_query(query_dict, frag, query_state_manager, llm_config, logger):
    query_type = query_dict.get("query_type")
    match query_type:
        case "new_rag_query":
            if query_state_manager.is_status_idle() is False:
                return { "response": "busy" }
                
            # Reset object
            query_state_manager.reset_query()

            # Not busy, start new thread
            _ = threading.Thread(
                target=execute_new_rag_pipeline,
                args=(
                    query_dict,
                    frag,
                    query_state_manager,
                    llm_config,
                    logger,
                ),
            ).start()
            return { "response": query_state_manager.get_query_id() }
        
        case "rag_query_status":
            return { "response": query_state_manager.get_query_slice() }
        
        case "cancel_rag_query":
            query_state_manager.set_status_cancelled()
            return { "response": "OK" }

def execute_new_rag_pipeline(query_dict, frag, query_state_manager, llm_config, logger):
    query_state_manager.set_status_active()
    
    llm_api = LLMAPI(llm_config, logger)

    rag_query = RAGQuery(query_dict, llm_api, frag, query_state_manager, llm_config, logger)
    rag_query.execute()