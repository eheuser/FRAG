class ChatObject {
    constructor() {
        this.url = getBaseUrl();

        // Data URL's
        this.query_url = `${this.url}/query`;
        this.rag_url = `${this.url}/stream`;

        // Configuration Options
        this.doc_multi_hit = false;
        this.max_shard_ctx = 3;
        this.n_results = 100;

        // History
        this.chat_history = [ ];
        this.reasoner_output = [ ];
        this.context_events = [ ];
        this.text_search_results = [ ];

        // State
        this.collapse_ids = { };

        let chat_output = document.getElementById("chat_output");
        this.frag_chat = chat_output.innerHTML;
    }

    clear_history() {
        this.chat_history = [ ];
        this.reasoner_output = [ ];
        this.context_events = [ ];

        this.collapse_ids = { };

        let chat_output = document.getElementById("chat_output");
        let reasoner_output = document.getElementById("reasoner_output");
        let event_output = document.getElementById("event_output");

        if (reasoner_output) {
            reasoner_output.innerHTML = "";
        }

        if (chat_output) {
            chat_output.innerHTML = this.frag_chat;
        }

        if (event_output) {
            event_output.innerHTML = "";
        }
    }

    async expand_chat_evt() {
        for (let [dom_id, _] of Object.entries(this.collapse_ids)) {
            let collapse_btn = document.getElementById(`${dom_id}_btn`);
            if (collapse_btn) {
                if (collapse_btn.classList.contains("bi-plus-lg")) {
                    await toggle_event(collapse_btn, dom_id)
                }
            }
        }
    }

    async collapse_chat_evt() {
        for (let [dom_id, _] of Object.entries(this.collapse_ids)) {
            let collapse_btn = document.getElementById(`${dom_id}_btn`);
            if (collapse_btn) {
                if (collapse_btn.classList.contains("bi-dash-lg")) {
                    await toggle_event(collapse_btn, dom_id)
                }
            }
        }
    }
    
    get_context_event_string() {
        return this.context_events.join("\n");
    }

    add_context_event(event) {
        let event_output = document.getElementById("event_output");

        let dom_id = getUuid();
        this.context_events.push( [ event, dom_id ] );

        event_output.insertAdjacentHTML("beforeend", this.get_ctx_event_html(marked.parse(event), dom_id));
    }

    clear_context_events() {
        this.context_events = [ ];
        let event_output = document.getElementById("event_output");
        if (event_output) {
            event_output.innerHTML = ``;
        }
    }

    clear_reasoner() {
        let reasoner_output = document.getElementById("reasoner_output");

        if (reasoner_output) {
            reasoner_output.innerHTML = ``;
        }
    }

    async highlight_event_output() {
        //let event_highlight_input = document.getElementById("event_highlight_input");
        let event_highlight_badge = document.getElementById("event_highlight_badge");

        let total_cnt = 0;

        let highlight_value = getFilterValue("event_highlight_input");
        
        for (let idx = 0; idx < this.context_events.length; idx++) {
            let event = this.context_events[idx][0];
            let dom_id = this.context_events[idx][1];

            let elem = document.getElementById(dom_id);
            
            if (elem) {
                if (highlight_value != null) {
                    let outer_elem = document.getElementById(`${dom_id}_outer`);
                    if ((typeof (highlight_value) === 'string') && (highlight_value != "") && (!(`${event}`.toLocaleLowerCase().includes(highlight_value)))) {
                        if (outer_elem) {
                            outer_elem.style.visibility = "hidden";
                            outer_elem.style.height = "0px";
                            if (outer_elem.classList.contains("mb-2")) {
                                outer_elem.classList.remove("mb-2");
                            }
                        }
                    } else {
                        if (outer_elem) {
                            outer_elem.style.visibility = "visible";
                            outer_elem.style.height = "auto";
                            if ( !(outer_elem.classList.contains("mb-2")) ) {
                                outer_elem.classList.add("mb-2");
                            }
                        }
                    }
                    let out_arr = highlightString(event, highlight_value);
                    let res = out_arr[0];
                    let cnt = out_arr[1];
                    total_cnt += cnt;
                    elem.innerHTML = res;
                } else {
                    elem.innerHTML = event;
                }
            }
        }
        if (total_cnt > 99) {
            event_highlight_badge.innerText = `99+`;
        } else {
            event_highlight_badge.innerText = total_cnt.toLocaleString();
        }
        
    }

    add_chat_history(speaker, text, dom_id) {
        this.chat_history.push( [ speaker, text, dom_id ] );
    }

    update_last_chat_output(token) {
        let idx = this.chat_history.length - 1;
        if (idx >= 0) {
            this.chat_history[idx][1] = `${this.chat_history[idx][1]}${token}`;
            return this.chat_history[idx][1];
        }
        return "";
    }

    async highlight_chat_output() {
        let enable_llm_generation = document.getElementById("enable_llm_generation");
        if (enable_llm_generation.classList.contains("active") === true) {
            let idx = this.chat_history.length - 1;
            let chat_highlight_badge = document.getElementById("chat_highlight_badge");

            let total_cnt = 0;

            if (idx >= 0) {
                let msg = this.chat_history[idx][1];
                let response_output = document.getElementById(this.chat_history[idx][2]);

                if (response_output != null) {
                    //let reasoner_highlight_input = document.getElementById("reasoner_highlight_input");

                    let highlight_value = getFilterValue("reasoner_highlight_input");
                    if (highlight_value) {
                        let out_arr = highlightString(msg, highlight_value);
                        let res = out_arr[0];
                        let cnt = out_arr[1];
                        total_cnt += cnt;
                        response_output.innerHTML = marked.parse(res);
                    } else {
                        response_output.innerHTML = marked.parse(msg);
                    }
                }
            }
            if (total_cnt > 99) {
                chat_highlight_badge.innerText = `99+`;
            } else {
                chat_highlight_badge.innerText = total_cnt.toLocaleString();
            }
        } else {
            this.add_agent_response();
        }
    }

    add_reasoner_output(text, dom_id) {
        this.reasoner_output.push( [ text, dom_id] );
    }

    update_last_reasoner_output(token) {
        let idx = this.reasoner_output.length - 1;
        if (idx >= 0) {
            this.reasoner_output[idx][0] = `${this.reasoner_output[idx][0]}${token}`;
            return this.reasoner_output[idx][0];
        }
        return "";
    }

    async highlight_reasoner_output() {
        let idx = this.reasoner_output.length - 1;
        let reasoner_highlight_badge = document.getElementById("reasoner_highlight_badge");

        let total_cnt = 0;

        if (idx >= 0) {
            let reasoner = this.reasoner_output[idx][0];
            let reasoner_response_output = document.getElementById(this.reasoner_output[idx][1]);

            if (reasoner_response_output != null) {
                //let reasoner_highlight_input = document.getElementById("reasoner_highlight_input");

                let highlight_value = getFilterValue("reasoner_highlight_input");
                if (highlight_value) {
                    let out_arr = highlightString(reasoner, highlight_value);
                    let res = out_arr[0];
                    let cnt = out_arr[1];
                    total_cnt += cnt;
                    reasoner_response_output.innerHTML = marked.parse(res);
                } else {
                    reasoner_response_output.innerHTML = marked.parse(reasoner);
                }
            }
        }

        if (total_cnt > 99) {
            reasoner_highlight_badge.innerText = `99+`;
        } else {
            reasoner_highlight_badge.innerText = total_cnt.toLocaleString();
        }
    }

    async display_no_results() {
        let chat_output = document.getElementById("chat_output");
        let response = `` +
            `<h5 class="text-center text-secondary mt-5">No Results Found</h5>` +
            ``;
        chat_output.insertAdjacentHTML("beforeend", response);
    }

    async cancel_rag_search(elem) {
        if (elem.classList.contains("bi-x-lg")) {
            elem.classList.remove("bi-x-lg");
        }
        if (elem.classList.contains("btn-outline-danger")) {
            elem.classList.remove("btn-outline-danger");
            elem.classList.add("btn-danger");
        }

        elem.innerHTML = `<div class="spinner-border spinner-border-sm text-light" style="margin-bottom: 2px;" role="status"></div>`;
        let res = await postApiJson(
            this.rag_url,
            {
                "query_type": "cancel_rag_query",
            },
        );

        await new Promise(r => setTimeout(r, 1_000));
        //if ( ("response" in res) && (res.response === "OK") ) {
        //    this.clear_history();
        //}

        elem.innerHTML = ``;
        if ( !(elem.classList.contains("bi-x-lg")) ) {
            elem.classList.add("bi-x-lg");
        }
        if (elem.classList.contains("btn-danger")) {
            elem.classList.remove("btn-danger");
            elem.classList.add("btn-outline-danger");
        }
    }

    async reset_chat(elem) {
        if (elem.classList.contains("bi-trash")) {
            elem.classList.remove("bi-trash");
        }
        if (elem.classList.contains("btn-outline-primary")) {
            elem.classList.remove("btn-outline-primary");
            elem.classList.add("btn-primary");
        }

        elem.innerHTML = `<div class="spinner-border spinner-border-sm text-light" style="margin-bottom: 2px;" role="status"></div>`;

        await new Promise(r => setTimeout(r, 500));
        this.clear_history();
        await new Promise(r => setTimeout(r, 500));

        elem.innerHTML = ``;
        if ( !(elem.classList.contains("bi-trash")) ) {
            elem.classList.add("bi-trash");
        }
        if (elem.classList.contains("btn-primary")) {
            elem.classList.remove("btn-primary");
            elem.classList.add("btn-outline-primary");
        }
    }

    async enable_clear_btn() {
        let reset_query_button = document.getElementById("reset_query_button");
        if (reset_query_button) {
            if (reset_query_button.classList.contains("disabled")) {
                reset_query_button.classList.remove("disabled");
            }
        }
    }

    async disable_clear_btn() {
        let reset_query_button = document.getElementById("reset_query_button");
        if (reset_query_button) {
            if ( !(reset_query_button.classList.contains("disabled")) ) {
                reset_query_button.classList.add("disabled");
            }
        }
    }

    async execute_rag_search() {
        // clear events
        this.clear_context_events();
        // clear reasoner
        this.clear_reasoner();
        // disable clear button
        this.disable_clear_btn();

        // remove dom_id
        let chat_history = [ ];
        for (let idx = 0; idx < this.chat_history.length; idx++ ) {
            chat_history.push(
                [
                    this.chat_history[idx][0],
                    this.chat_history[idx][1],
                ]
            );
        }

        // Reasoner output toggle
        let verbose = false;
        let verbose_reasoner_output = document.getElementById("verbose_reasoner_output");
        if (verbose_reasoner_output) {
            verbose = verbose_reasoner_output.checked;
        }

        let res = await postApiJson(
            this.rag_url,
            {
                "query_list": chat_history,
                "query_type": "new_rag_query",
                "verbose_reasoner": verbose,
            },
        );
        
        let query_id;
        if ( (res) && (res.response) && (res.response != "busy")) {

        }
        if ( !(res) ) {
            // TODO
            // { "response": "busy" }
            this.enable_clear_btn();
            return;
        }

        let cancel_query_btn = document.getElementById("cancel_query_btn");
        if (cancel_query_btn.classList.contains("disabled")) {
            cancel_query_btn.classList.remove("disabled");
        }

        let chat_output = document.getElementById("chat_output");
        let reasoner_output = document.getElementById("reasoner_output");

        let dom_id = getUuid();
        let agent_response = this.get_agent_response_html(null, "text", getAnimatetdLoadingStr(""), dom_id);

        let reasoner_dom_id = getUuid();
        let reasoner_response = this.get_reasoner_response_html(reasoner_dom_id);

        chat_output.insertAdjacentHTML("beforeend", agent_response);
        reasoner_output.insertAdjacentHTML("beforeend", reasoner_response);

        let response_output = document.getElementById(dom_id);
        let reasoner_response_output = document.getElementById(reasoner_dom_id);
        this.add_reasoner_output("", reasoner_dom_id);

        let llm_generation_status = document.getElementById("llm_generation_status");

        let follow_reasoner_output = document.getElementById("follow_reasoner_output");
        let follow_chat_output = document.getElementById("follow_chat_output");
        
        let user_scroll = false;
        let reasoner_scroll = false;

        chat_output.addEventListener("scroll", function() {
            let is_at_bottom = chat_output.scrollHeight - chat_output.scrollTop === chat_output.clientHeight;
            
            if (!is_at_bottom) {
                user_scroll = true;
                follow_chat_output.style.visibility = "visible";
            } else {
                user_scroll = false;
                follow_chat_output.style.visibility = "hidden";
            }
        });

        reasoner_output.addEventListener("scroll", function() {
            let is_at_bottom = reasoner_output.scrollHeight - reasoner_output.scrollTop === reasoner_output.clientHeight;
            
            if (!is_at_bottom) {
                reasoner_scroll = true;
                follow_reasoner_output.style.visibility = "visible";
            } else {
                reasoner_scroll = false;
                follow_reasoner_output.style.visibility = "hidden";
            }
        });

        let chat_update_ms = 50;
        let msg = "";
        let reasoner = "";

        let last_llm_status = null;

        while (true) {
            await new Promise(r => setTimeout(r, chat_update_ms));

            let token = await postApiJson(
                this.rag_url,
                {
                    "query_type": "rag_query_status",
                },
            );

            if ( !(token) || !(token.response)) {
                break;
            }
            let updated_dom = false

            // Update reasoner window
            if (token.response.reasoner.length > 0) {
                reasoner = this.update_last_reasoner_output(token.response.reasoner);

                //let reasoner_highlight_input = document.getElementById("reasoner_highlight_input");
                let reasoner_highlight_badge = document.getElementById("reasoner_highlight_badge");

                let highlight_value = getFilterValue("reasoner_highlight_input");
                if (highlight_value) {
                    let out_arr = highlightString(reasoner, highlight_value);
                    let res = out_arr[0];
                    let cnt = out_arr[1];
                    if (cnt > 99) {
                        cnt = `99+`;
                    } else {
                        cnt = cnt.toLocaleString();
                    }
                    reasoner_response_output.innerHTML = marked.parse(res);
                    reasoner_highlight_badge.innerText = cnt;
                } else {
                    reasoner_response_output.innerHTML = marked.parse(reasoner);
                    reasoner_highlight_badge.innerText = 0;
                }
                updated_dom = true;
            }

            // Update main chat window
            // structure: { "status": "str", "msg": "str", "reasoner": "str", "events": [list], "last_update": "float", "id": "str" }
            if (token.response.msg.length > 0) {
                msg = this.update_last_chat_output(token.response.msg);

                //let chat_highlight_input = document.getElementById("chat_highlight_input");
                let chat_highlight_badge = document.getElementById("chat_highlight_badge");

                let highlight_value = getFilterValue("chat_highlight_input");
                if (highlight_value) {
                    let out_arr = highlightString(msg, highlight_value);
                    let res = out_arr[0];
                    let cnt = out_arr[1];
                    if (cnt > 99) {
                        cnt = `99+`;
                    } else {
                        cnt = cnt.toLocaleString();
                    }
                    response_output.innerHTML = marked.parse(res);
                    chat_highlight_badge.innerText = cnt;
                } else {
                    response_output.innerHTML = marked.parse(msg);
                    chat_highlight_badge.innerText = 0;
                }
                updated_dom = true;
            }

            // Update events window
            if (token.response.events.length > 0) {
                for (let idx = 0; idx < token.response.events.length; idx++) {
                    let event = token.response.events[idx];
                    this.add_context_event(event);
                }
                updated_dom = true;
                
            }

            // Speed up or slow down the update
            if (updated_dom === true) {
                chat_update_ms = 50;
            } else {
                chat_update_ms = 200;
            }
            //console.log(token.response.status);
            if (last_llm_status != token.response.status) {
                llm_generation_status.innerHTML = `${getAnimatetdLoadingStr(token.response.status, false)}`;
                last_llm_status = token.response.status;
                if (llm_generation_status.classList.contains("btn-outline-secondary")) {
                    llm_generation_status.classList.remove("btn-outline-secondary");
                    llm_generation_status.classList.add("btn-outline-success");
                }
            }
            if (token.response.status == "Idle") {
                llm_generation_status.innerHTML = "Idle";
                if (llm_generation_status.classList.contains("btn-outline-success")) {
                    llm_generation_status.classList.remove("btn-outline-success");
                    llm_generation_status.classList.add("btn-outline-secondary");
                }
                break;
            }

            if (!user_scroll) {
                chat_output.scrollTop = chat_output.scrollHeight;
            }
            if (!reasoner_scroll) {
                reasoner_output.scrollTop = reasoner_output.scrollHeight;
            }
        }
        
        if (!user_scroll) {
            chat_output.scrollTop = chat_output.scrollHeight;
        }
        if (!reasoner_scroll) {
            reasoner_output.scrollTop = reasoner_output.scrollHeight;
        }
        if ( !(cancel_query_btn.classList.contains("disabled")) ) {
            cancel_query_btn.classList.add("disabled");
        }
        
        this.enable_clear_btn();
    }

    async execute_text_search(text, condition_dict=null) {
        this.clear_history();

        await this.add_user_query(text, true);

        let results = await postApiJson(
            this.query_url,
            {
                "query_string": text,
                "doc_multi_hit": this.doc_multi_hit,
                "max_shard_ctx": this.max_shard_ctx,
                "n_results": this.n_results,
                "condition_dict": condition_dict
            },
        );

        if ( (results) && (results.length > 0) ) {
            this.text_search_results = results;
            await this.add_agent_response();
        } else {
            await this.display_no_results();
        }
    }

    async add_user_query(text, clear=false) {
        let chat_output = document.getElementById("chat_output");
        if (clear === true) {
            chat_output.innerHTML = ``;
            this.clear_history();
        }
        
        let dom_id = getUuid();
        this.add_chat_history("user", text, dom_id);

        let user_query = `` +
            `<div class="row px-0 mb-3">` +
                `<div class="col col-1 pe-1 pt-2">` +
                    `<div class="btn btn-sm btn-emerge-flat bi-copy" style="float: right;border-radius: 999px;" onclick="copyDiv2Clipboard('${dom_id}');"></div>` +
                `</div>` +
                `<div class="col col-10 px-0 mx-0">` +
                    `<div class="card u-card shadow">` +
                        `<div class="card-body">` +
                            `<pre id="${dom_id}">` +
                                `${escapeHtml(text)}` +
                            `</pre>` +
                        `</div>` +
                    `</div>` +
                `</div>` +
                `<div class="col col-1">` +
                    `<div class="circle-icon u-icon mt-2">` +
                        `<span class="bi bi-person-fill" style="font-size: 28px;"></span>` +
                    `</div>` +
                `</div>` +
            `</div>`;
        chat_output.innerHTML = `${chat_output.innerHTML}\n${user_query}`; 
    }

    async add_agent_response() {
        let total_cnt = 0;
        let chat_highlight_badge = document.getElementById("chat_highlight_badge");
        let chat_highlight_input = getFilterValue("chat_highlight_input");
        let chat_output = document.getElementById("chat_output");
        // clear output
        chat_output.innerHTML = ``;

        let last_idx = this.text_search_results.length - 1;
        for ( let idx=0; idx < this.text_search_results.length; idx++ ) {
            let doc = `${this.text_search_results[idx].event}`;

            let result_string;
            let language = ``;
            // highlight structured output from the parsers.
            if (doc.startsWith("{") || doc.startsWith("[")) {
                let result = hljs.highlightAuto(doc);
                language = `language-${result.language}`;
                let out_arr = highlightString(result.value, chat_highlight_input);
                result_string = out_arr[0];
                let cnt = out_arr[1];
                total_cnt += cnt;
            } else {
                let out_arr = highlightString(doc, chat_highlight_input);
                result_string = out_arr[0];
                let cnt = out_arr[1];
                total_cnt += cnt;
            }

            let meta = hljs.highlightAuto(JSON.stringify(this.text_search_results[idx].meta, null, 2));
            let dom_id = getUuid();
            let agent_response = this.get_agent_response_html(meta.value, language, result_string, dom_id);
            if (idx != last_idx) {
                agent_response = `${agent_response}` + `<div class="row px-0 py-0 my-0 my-2" style="height: 4px;border-radius: 2px;background-color: #aaaaaa40;"></div>`;
            }
            chat_output.insertAdjacentHTML("beforeend", agent_response);
            this.add_chat_history("assistant", result_string, dom_id);
        }
        if (total_cnt > 99) {
            chat_highlight_badge.innerText = `99+`;
        } else {
            chat_highlight_badge.innerText = total_cnt.toLocaleString();
        }
        try {
            //hljs.highlightAll();
        } catch (err) {
            //console.warn(err);
        }
    }

    get_ctx_event_html(event, dom_id) {
        let collapse_id = getUuid();
        this.collapse_ids[collapse_id] = true;

        return `` +
            `<div class="row px-3 mb-2"  id="${dom_id}_outer">` +
                `<div class="card a-card pe-1">` +
                    `<div class="btn-toolbar px-0 py-0" role="group">` +
                        `<div class="flex-grow-1"></div>` +
                        `<button class="btn btn-sm btn-emerge bi bi-copy fw-bolder mt-1 me-2" style="border-radius: 999px;" type="button" onclick="copyDiv2Clipboard('${dom_id}');" title="Copy Event"></button>` + 
                        `<button class="btn btn-sm btn-emerge bi bi-plus-lg fw-bolder mt-1" style="border-radius: 999px;" type="button" onclick="toggle_event(this, '${collapse_id}');" id="${collapse_id}_btn" title="Expand or minimize event"></button>` +
                    `</div>` +
                    `<div class="partial-collapse" id="${collapse_id}">` +
                        `<div class="card-body px-2 pt-2">` +
                            `<pre>` +
                                `<code id="${dom_id}">` +
                                    `${event}` +
                                `</code>` +
                            `</pre>` +
                        `</div>` +
                    `</div>` +
                `</div>` +
            `</div>`;
    }

    get_reasoner_response_html(dom_id) {
        if (dom_id === null) {
            dom_id = getUuid();
        }
        
        return `` +
            `<div class="row px-3 mb-3">` +
                `<div class="card a-card">` +
                    `<div class="card-body px-0">` +
                        `<pre>` +
                            `<code id="${dom_id}">` +
                            `</code>` +
                        `</pre>` +
                    `</div>` +
                `</div>` +
            `</div>`;
    }

    get_agent_response_html(file_info, language, result_pages, dom_id=null) {
        if (dom_id === null) {
            dom_id = getUuid();
        }
        let result_header = `<b>Result Pages</b></br>`;
        if (file_info === null) {
            result_header = "";
            file_info = "";
        } else {
            file_info = `` +
                `<pre>` +
                    `<b>File Information</b></br>` +
                    `<code class="language-json">` +
                        `${file_info}` +
                    `</code>` +
                `</pre>`;
        }

        this.add_chat_history("assistant", "", dom_id);

        return `` +
            `<div class="row px-0  mb-3">` +
                `<div class="col col-1 pt-0 pe-0">` +
                    `<div class="circle-icon mt-1 me-2" style="float: right;">` +
                        `<img src="../img/android-chrome-192x192.png" alt="FRAG Agent">` +
                    `</div>` +
                `</div>` +
                `<div class="col col-10 px-0 mx-0">` +
                    `<div class="card a-card">` +
                        `<div class="card-body px-3">` +
                                `${file_info}` +
                            `<pre>` +
                                `${result_header}` +
                                `<code class="${language}" id="${dom_id}">` +
                                    `${result_pages}` +
                                `</code>` +
                            `</pre>` +
                        `</div>` +
                    `</div>` +
                `</div>` +
                `<div class="col col-1 ps-1 pt-2">` +
                    `<div class="btn btn-sm btn-emerge-flat bi-copy" style="border-radius: 999px;" onclick="copyDiv2Clipboard('${dom_id}');"></div>` +
                `</div>` +
            `</div>`;
    }
}

const highlightReasonerOutput = async function() {
    chat_obj.highlight_reasoner_output();
}

const highlightChatOutput = async function() {
    chat_obj.highlight_chat_output();
}

const highlightEventOutput = async function() {
    chat_obj.highlight_event_output();
}

const toggle_event = async function(btn, collapse_id) {
    let collapse_block = document.getElementById(collapse_id);

    if (collapse_block.classList.contains("expanded")) {
        collapse_block.classList.remove("expanded");
        if (btn.classList.contains("bi-dash-lg")) {
            btn.classList.remove("bi-dash-lg");
            btn.classList.add("bi-plus-lg");
        }
        
    } else {
        collapse_block.classList.add("expanded");
        if (btn.classList.contains("bi-plus-lg")) {
            btn.classList.remove("bi-plus-lg");
            btn.classList.add("bi-dash-lg");
        }
    }
}

const followOutput = async function(dom_id) {
    elem = document.getElementById(dom_id);
    if (elem) {
        elem.scrollTop = elem.scrollHeight;
    }
}

const expandChatEvt = async function() {
    await chat_obj.expand_chat_evt();
}

const collapseChatEvt = async function() {
    await chat_obj.collapse_chat_evt();
}

const cancelRagSearch = async function(elem) {
    await chat_obj.cancel_rag_search(elem);
}

const resetChat = async function(elem) {
    await chat_obj.reset_chat(elem);
}