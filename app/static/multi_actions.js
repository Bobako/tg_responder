function multi_actions() {
    if ($("input[type=checkbox]:checked").length != 0) {
        $(".multiple_actions").addClass("multiple_actions_extended");
    }
    else{
        $(".multiple_actions").removeClass("multiple_actions_extended");
    }
}

function toggle(aid, class_){
    let req = new XMLHttpRequest();
    req.open("GET", "api/toggle?id="+aid+"&class="+class_, true);
    req.send();
}

function multi_actions_activated(type, class_){
    let cbs = $("input.ma:checked");
    let aid = "";
    for (let i = 0; i < cbs.length; i ++){
        aid += $(cbs[i]).attr("id").slice(2) + "-";
        }
    aid = aid.slice(0, -1);
    if (type == "toggle"){
        let req = new XMLHttpRequest();
        req.open("GET", "api/toggle?class="+class_+"&id="+aid, true);
        req.send();
        return;
    }
    if (type == "delete"){
        popUp("Вы уверены?", "api/delete?class="+class_+"&id="+aid);
        return;
    }
    if (type == "share"){
        sharePopUp(aid, "share")
    }

    if (type == "delete_derived"){
        sharePopUp(aid, "delete_derived")
    }

}

function popUp(text, url){
$("body").append(
'<div class="popup">'+
'    <p>'+ text +
'    </p>'+
'    <div class="buttons">'+
'        <button class="action" onclick="$(`.popup`).remove()">Нет</button>'+
'        <button class="action" onclick=accept(`'+url+'`)>Да</button>'+
'    </div>'+
'</div>'
);
}

function accept(url=""){
    if (url != ""){
        let req = new XMLHttpRequest();
        req.open("GET", url, true);
        req.send();
        req.onload = function(){
            $(".popup").remove();
            window.location.href = "";}
    }

}

function sharePopUp(cids, action){
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    const account_id = urlParams.get('account_id')
    let req = new XMLHttpRequest();
    req.open("GET", "api/get_accounts_to_share?account_id="+account_id+"&cids="+cids + "&action="+action, true);
    req.send();
    req.onload = function () {
        $("body").append(req.response);
    }
}

