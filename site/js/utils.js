const postApiJson = async function(url, data_obj) {
    let response;
    try {
        response = await fetch(url, {
            redirect: "manual",
            method: "POST",
            headers: {
                "content-type": "application/json"
            },
            body: JSON.stringify(data_obj)
        });
        let data = await response.json();
        return data;
    }
    catch (err) {
        console.warn(err);
        return {};
    }
}

const getApiJson = async function(path) {
    let url = `${getBaseUrl()}/${path}`;

    let response;
    try {
        response = await fetch(url, { redirect: "manual" });
        let data = await response.json();
        return data;
    }
    catch (err) {
        console.warn(err);
        return {};
    }
}

const getBaseUrl = function() {
    // Build URL base
    let protocol = `${window.location.protocol}//`;
    let port = ``
   if (window.location.port) {
       port = `:${window.location.port}`;
   }
   let api_host_name = window.location.hostname;
   let url = `${protocol}${api_host_name}${port}`;
   return url;
}

const getFilterValue = function(dom_id, escape=true) {
    let el = document.getElementById(dom_id);
    if (el) {
        if (el.value == "") {
            return null;
        } else if (escape === false) {
            let filter_str  = `${el.value}`.toLocaleLowerCase();
            return filter_str;
        } else {
            let filter_str  = `${el.value}`.toLocaleLowerCase().replaceAll(`\\`, `\\\\`);
            return filter_str;
        }
    } else {
        return null;
    }
}

const getUuid = function() {
    let dt = new Date().getTime();
    let uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        let r = (dt + Math.random() * 16) % 16 | 0;
        dt = Math.floor(dt / 16);
        return (c == 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
    return uuid;
}

const getAnimatetdLoadingStr = function(text, bold=true) {
    // 3 dot's blinking in sequence
    let lb = ``;
    let rb = ``;
    if (bold === true) {
        lb = `<b>`;
        rb = `</b>`;
    }
    return `${lb}<span class="loader">${text}&nbsp;<span class="loader__dot">.</span><span class="loader__dot">.</span><span class="loader__dot">.</span></span>${rb}`;
}

const highlightString = function(_str, search_str, escape_slash=false) {
    // highlight strings fragments with <mark>
    _str = `${_str}`;
    if (!search_str || search_str === "" || search_str === "." || search_str === "\\") {
        return [_str, 0];
    }

    if (escape_slash === false) {
        search_str = search_str.replace(/\\\\/g, `\\`);
    }

    let escapeRegex = str => str.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'); 

    let search_parts = search_str.split('*').map(part => escapeRegex(part));
    let result = _str;
    let cnt = 0;

    for (let part of search_parts) {
        if (part) {
            let regex = new RegExp(part, 'gi');
            result = result.replace(regex, match => {
                cnt += 1;
                return `<mark>${match}</mark>`;
            });
        }
    }
    return [result, cnt];
}

async function copy2Clipboard(full_text, num=40) {
    // copy to clipboard
    if (!full_text) {
        return;
    }

    let copy_text = `${full_text}`;
    full_text = `${full_text}`;

    if (copy_text.length > num) {
        copy_text = copy_text.slice(0, num);
    }

    navigator.clipboard.writeText(full_text);
    document.getElementById("toastText").innerHTML = `${copy_text}`;
    let toast = new bootstrap.Toast(document.getElementById("liveToast"));
    toast.show();
}

escapeHtml = function(unsafe) {
    if (typeof(unsafe) != "string") {
        unsafe = `${unsafe}`;
    }
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

const closeAllModals = async function() {
    let modals = document.getElementsByClassName('modal-backdrop');
    for (let idx = 0; idx < modals.length; idx++) {
        modals[idx].remove();
    }
}