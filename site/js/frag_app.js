

const appMain = async function() {
    const submitQuery = async function() {
        let chat_submit = document.getElementById("chat_submit");
        let enable_llm_generation = document.getElementById("enable_llm_generation");

        // no double-submit
        chat_submit.removeEventListener("click", submitQuery);

        let saved_html = chat_submit.innerHTML;
        if (chat_submit.classList.contains("bi-arrow-up-circle")) {
            chat_submit.classList.remove("bi-arrow-up-circle");
        }
        chat_submit.innerHTML = `<div class="spinner-border spinner-border-sm text-light" role="status"></div>`;

        let chat_input = document.getElementById("chat_input");
        let text = chat_input.value;
        chat_input.value = ``;
        chat_input.dispatchEvent(new Event('input', { wake: true }));

        if (enable_llm_generation.classList.contains("active") === true) {
            await chat_obj.add_user_query(text, false);
            await chat_obj.execute_rag_search();
        } else {
            await chat_obj.execute_text_search(text);
        }

        if ( !(chat_submit.classList.contains("bi-arrow-up-circle")) ) {
            chat_submit.classList.add("bi-arrow-up-circle");
        }
        chat_submit.innerHTML = saved_html;
        chat_submit.addEventListener("click", submitQuery);
    }
    
    const toggleLLM = async function() {
        chat_obj.clear_history();

        let enable_llm_generation = document.getElementById("enable_llm_generation");
        
        if (enable_llm_generation.classList.contains("active") === false) {
            enable_llm_generation.innerHTML = `` +
                `<b class="ps-1">LLM Disabled</b>` +
                `<span class="bi bi-circle-fill text-danger ms-2 px-0 py-0"></span>`;
        } else {
            enable_llm_generation.innerHTML = `` +
                `<b class="ps-1">LLM Enabled</b>` +
                `<span class="bi bi-circle-fill text-success ms-2 px-0 py-0"></span>`;
        }
    }

    const bootStrap = async function() {
        // set auto-expand listener for chat window
        let textarea = document.getElementById("chat_input");
        textarea.addEventListener("input", () => {
            let chat_output = document.getElementById("chat_output");
            let reasoner_output = document.getElementById("reasoner_output");
            let event_output = document.getElementById("event_output");

            textarea.style.height = "auto";
            let max_height = 400;
            let new_height = textarea.scrollHeight;
            if (new_height > max_height) {
                new_height = max_height;
            }
            let default_chat_output_height = 344;
            let default_textarea_height = 54;
            // sync the two containers
            let new_chat_height = default_chat_output_height + (new_height - default_textarea_height);
            // apply
            textarea.style.height = `${new_height}px`;
            chat_output.style.height = `calc(100vh - ${new_chat_height}px)`;
            reasoner_output.style.height = `calc(100vh - ${new_chat_height}px)`;
            // account for the btn toolbar for expand/collapse + scroll top/bottom
            event_output.style.height = `calc(100vh - ${new_chat_height}px)`;
        });

        // set listener for submit button
        let chat_submit = document.getElementById("chat_submit");
        chat_submit.addEventListener("click", submitQuery);

        // set listener for LLM + RAG or Similarity search toggle
        let enable_llm_generation = document.getElementById("enable_llm_generation");
        enable_llm_generation.addEventListener("click", toggleLLM);

        // Highlighters
        const reasoner_highlight_input = document.getElementById("reasoner_highlight_input");

        reasoner_highlight_input.addEventListener("input", function() {
          highlightReasonerOutput();
        });

        const chat_highlight_input = document.getElementById("chat_highlight_input");

        chat_highlight_input.addEventListener("input", function() {
            highlightChatOutput();
        });

        const event_highlight_input = document.getElementById("event_highlight_input");

        event_highlight_input.addEventListener("input", function() {
            highlightEventOutput();
        });
    };

    // start app
    await bootStrap();
}

const copyDiv2Clipboard = async function(dom_id) {
    let elem = document.getElementById(dom_id);
    if (elem) {
        copy2Clipboard(elem.innerText);
    }
}

const copyEvents2Clipboard = async function(elem) {
    copy2Clipboard(chat_obj.get_context_event_string());
}

const scrollToBottom = async function(dom_id) {
    elem = document.getElementById(dom_id);
    if (elem) {
        elem.scrollTop = elem.scrollHeight;
    }
}

const scrollToTop = async function(dom_id) {
    elem = document.getElementById(dom_id);
    if (elem) {
        elem.scrollTop = 0;
    }
}

const scrollPageUp = async function(dom_id) {
    elem = document.getElementById(dom_id);
    if (elem) {
        let page_height = window.innerHeight - 340;
        elem.scrollBy(0, -page_height)
    }
}

const scrollPageDown = async function(dom_id) {
    elem = document.getElementById(dom_id);
    if (elem) {
        let page_height = window.innerHeight - 340;
        elem.scrollBy(0, page_height);
    }
}
// Create Chat object and start the app shell
const chat_obj = new ChatObject();

appMain();