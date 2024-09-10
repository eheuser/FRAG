// Controls the static Modals

const loadLlmConfig = async function() {
    let config_form_api_url = document.getElementById("config_form_api_url");
    let config_form_api_key = document.getElementById("config_form_api_key");
    let config_form_model = document.getElementById("config_form_model");
    let config_form_ctx = document.getElementById("config_form_ctx");
    let config_form_ctx_max = document.getElementById("config_form_ctx_max");
    let config_form_timeout = document.getElementById("config_form_timeout");
    let config_form_temperature = document.getElementById("config_form_temperature");

    let config_form_discard = document.getElementById("config_form_discard");
    let config_form_apply = document.getElementById("config_form_apply");

    let config = await getApiJson("config");
    if (config) {
        config_form_api_url.value = config.api_url;
        config_form_api_url.addEventListener("input", function() {
            modifyLlmConfig();
        });

        config_form_api_key.value = config.api_key;
        config_form_api_key.addEventListener("input", function() {
            modifyLlmConfig();
        });

        config_form_model.value = config.model;
        config_form_model.addEventListener("input", function() {
            modifyLlmConfig();
        });

        config_form_ctx.value = config.context;
        config_form_ctx.addEventListener("input", function() {
            modifyLlmConfig();
        });

        config_form_ctx_max.value = config.max_rag_context;
        config_form_ctx_max.addEventListener("input", function() {
            modifyLlmConfig();
        });

        config_form_timeout.value = config.timeout;
        config_form_timeout.addEventListener("input", function() {
            modifyLlmConfig();
        });

        config_form_temperature.value = config.temperature;
        config_form_temperature.addEventListener("input", function() {
            modifyLlmConfig();
        });
    }

    if ( !(config_form_discard.classList.contains("disabled")) ) {
        config_form_discard.classList.add("disabled");
    }
    if ( !(config_form_apply.classList.contains("disabled")) ) {
        config_form_apply.classList.add("disabled");
    }
}

const modifyLlmConfig = async function() {
    let config_form_discard = document.getElementById("config_form_discard");
    let config_form_apply = document.getElementById("config_form_apply");

    if (config_form_discard.classList.contains("disabled")) {
        config_form_discard.classList.remove("disabled");
    }
    if (config_form_apply.classList.contains("disabled")) {
        config_form_apply.classList.remove("disabled");
    }
    
}

const applyConfig = async function() {
    let config_form_api_url = document.getElementById("config_form_api_url");
    let config_form_api_key = document.getElementById("config_form_api_key");
    let config_form_model = document.getElementById("config_form_model");
    let config_form_ctx = document.getElementById("config_form_ctx");
    let config_form_ctx_max = document.getElementById("config_form_ctx_max");
    let config_form_timeout = document.getElementById("config_form_timeout");
    let config_form_temperature = document.getElementById("config_form_temperature");

    let config = {
        "api_url": `${config_form_api_url.value}`,
        "api_key": `${config_form_api_key.value}`,
        "model": `${config_form_model.value}`,
        "context": parseInt(config_form_ctx.value),
        "max_rag_context":parseInt(config_form_ctx_max.value),
        "timeout": parseFloat(config_form_timeout.value),
        "temperature": parseFloat(config_form_temperature.value),
    };
    
    let _ = await postApiJson(
        `${getBaseUrl()}/update_config`,
        {
            "config": config,
        },
    );

    await loadLlmConfig();
}

const clearLlmConfig = async function() {
    document.getElementById("config_form_api_url").value = "";
    document.getElementById("config_form_api_key").value = "";
    document.getElementById("config_form_model").value = "";
    document.getElementById("config_form_ctx").value = "";
    document.getElementById("config_form_ctx_max").value = "";
    document.getElementById("config_form_timeout").value = "";
    document.getElementById("config_form_temperature").value = "";

    await modifyLlmConfig();
}

const loadLlmFiles = async function() {
    let result = await getApiJson("artifact_files");
    if ( !("response" in result) || !(result.response) ) {
        return;
    }
    let artifact_files = result.response;
    let table_html = [ ];
    for (let idx = 0; idx < artifact_files.length; idx++ ) {
        let entry = artifact_files[idx];

        table_html.push(
            `<tr>` +
                `<th scope="row">${entry.filepath}</th>` +
                `<td>${parseInt(entry.file_sz).toLocaleString()}</td>` +
                `<td>${entry.file_type}</td>` +
                `<td>${parseInt(entry.item_count).toLocaleString()}</td>` +
            `</tr>`
        );
    }

    let artifact_file_table = document.getElementById("artifact_file_table");
    artifact_file_table.innerHTML = table_html.join("\n");
}

const showModal = async function(modal_name) {
    let modal = document.getElementById(modal_name);
    modal.addEventListener('click', function (e) {
        // Check if the modal is clicked, not an element inside the modal:
        if (e.target === e.currentTarget) {
            closeAllModals();
        }
    });

    let upload_modal = new bootstrap.Modal(modal);
    upload_modal.show();
    await new Promise(r => setTimeout(r, 500));
    return upload_modal;
}

const closeModal = async function(modal_name) {
    let modal = document.getElementById(modal_name);
    let upload_modal = new bootstrap.Modal(modal);
    upload_modal.toggle();
    await new Promise(r => setTimeout(r, 100));
}

const closeOpenModal = async function(modal) {
    modal.hide();
    await new Promise(r => setTimeout(r, 100));
}

const uploadArtifactFiles = async function(files) {
    updateUploadProgressBar(5, "upload_file_progress", `5%`);
    // Open Upload Modal
    let upload_modal = await showModal("upload_file_progress_modal");

    let file_cnt = 0;
    try {
        // Gather files
        var form_data = new FormData();
        
        for (var i = 0, file; file = files[i]; i++) {
            file_cnt += 1;
            form_data.append("file", file);
        }

        let url = `${getBaseUrl()}/upload`;
        let data = null;
        let http = new XMLHttpRequest();
        http.upload.addEventListener("progress", function (event) {
            let percent = parseInt((event.loaded / event.total) * 100);
            if (percent == 100) {
                updateUploadProgressBar(percent, "upload_file_progress", `Upload Complete`);
            } else if (percent > 0) {
                updateUploadProgressBar(percent, "upload_file_progress", `${percent}%`);
            }
        });
        http.onreadystatechange = function () {
            if (http.readyState == XMLHttpRequest.DONE) {
                data = JSON.parse(http.responseText);
            }
        }
        http.open("post", url);
        http.send(form_data);
        while (data === null) {
            await new Promise(r => setTimeout(r, 100));
        }

    } catch (err) {
        console.warn(err);
    }
    // Close Upload Modal
    await closeOpenModal(upload_modal);
    await new Promise(r => setTimeout(r, 500));

    // Update modal counter
    let parse_file_progress_title = document.getElementById("parse_file_progress_title");
    parse_file_progress_title.innerHTML = `Parsing ${file_cnt.toLocaleString()} Artifacts`;

    updateUploadProgressBar(5, "parse_file_progress", `5%`)
    // Open File Parsing Modal and monitor
    let parse_modal = await showModal("parse_file_progress_modal");

    while (true) {
        let result = await getApiJson("progress");
        if ( (result) && (result.response) ) {
            let response = result.response;
            let completed = 0;
            let total = 0;
            for (let [filepath, status] of Object.entries(response)) {
                total += 1;
                if (status.status == "done") {
                    completed += 1;
                }
            }
            if (total == completed) {
                updateUploadProgressBar(100, "parse_file_progress", `Parsing Complete`);
                await new Promise(r => setTimeout(r, 500));
                break;
            } else if (completed > 0) {
                let percent = parseInt((completed / total) * 100);
                updateUploadProgressBar(percent, "parse_file_progress", `${percent}%`);
                await loadLlmFiles();
            }
            await new Promise(r => setTimeout(r, 500));
        }
    }

    // Close File Parse Modal
    await closeOpenModal(parse_modal);
    await loadLlmFiles();

    // Clear upload dialog
    document.getElementById("artifact_file_upload").value = ``;
}

const updateUploadProgressBar = function (perc, dom_id, text=null) {
    let elem = document.getElementById(dom_id);
    if (elem) {
        if (perc >= 100) {
            if (text != null) {
                elem.style.width = `100%`;
                elem.innerText = `${text}`;
            } else {
                elem.style.width = `100%`;
                elem.innerText = `100%`;
            }
        } else {
            if (text != null) {
                elem.style.width = `${perc}%`;
                elem.innerText = `${text}`;
            } else {
                elem.style.width = `${perc}%`;
                elem.innerText = `${perc}%`;
            }
        }
    }
}

const deleteVectorDB = async function(btn) {
    let saved_html = btn.innerHTML;

    if (btn.classList.contains("btn-outline-danger")) {
        btn.classList.remove("btn-outline-danger");
        btn.classList.add("btn-danger");
    }

    btn.innerHTML = `<div class="spinner-border spinner-border-sm text-light" style="margin-bottom: 2px;" role="status"></div>`;

    let result = await getApiJson("delete_db");
    await new Promise(r => setTimeout(r, 500));

    btn.innerHTML = saved_html;
    if (btn.classList.contains("btn-danger")) {
        btn.classList.remove("btn-danger");
        btn.classList.add("btn-outline-danger");
    }

    // Re-open the artifact files modal
    await new Promise(r => setTimeout(r, 100));
    await openArtifactModal();
    await loadLlmFiles();
}

const openArtifactModal = async function() {
    document.getElementById("files_modal_mm_btn").click();
}