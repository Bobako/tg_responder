$(document).ready(function(){
    sendRequest();
    setInterval(sendRequest, 500);

});

function sendRequest(){
    let req = new XMLHttpRequest();
    req.open("GET", "api/account_status", true);
    req.overrideMimeType("application/json");
    req.send();
    req.onload = function(){
        setStatuses(JSON.parse(req.response));
    };
}

function setStatuses(statuses){
    for (const [id, status] of Object.entries(statuses)) {
        let indicator = $("#account"+id).find(".indicator");
        if (status == 1){
            indicator.addClass("status1");
            indicator.removeClass("status-1");
            indicator.attr("title", "Активен");
        }
        if (status == -1){

            indicator.addClass("status-1");
            indicator.removeClass("status1");
            indicator.attr("title", "Не удалось подключиться");
        }
        if (status == 0){
            indicator.removeClass("status1");
            indicator.removeClass("status-1");
            indicator.attr("title", "Отключен");
        }
    }
}