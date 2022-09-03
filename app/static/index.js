function toggleAccount(aid){
    let req = new XMLHttpRequest();
    req.open("GET", "api/toggle?aid="+aid, true);
    req.send();
}

function multi_actions_activated(type){
    let cbs = $("input:checked");
    let aid = "";
    for (let i = 0; i < cbs.length; i ++){
        aid += $(cbs[i]).parent().parent().attr("id").slice(7) + "-";
        }
    aid = aid.slice(0, -1);
    if (type == "toggle"){
        let req = new XMLHttpRequest();
        req.open("GET", "api/toggle?class=Account&id="+aid, true);
        req.send();
        return;
    }
    if (type == "delete"){
    console.log("delete");
        popUp("Вы уверены?", "api/delete?class=Account&id="+aid);
        return;
    }
}

function popUp(text, url){
$("body").append(
'<div class="popup">'+
'    <p>'+ text +
'    </p>'+
'    <div class="buttons">'+
'        <button class="action" onclick="accept()">Нет</button>'+
'        <button class="action" onclick=accept(`'+url+'`)>Да</button>'+
'    </div>'+
'</div>'
);
}

function accept(url=""){
console.log(url);
    if (url != ""){
        let req = new XMLHttpRequest();
        req.open("GET", url, true);
        req.send();
    }
    $(".popup").remove();
}