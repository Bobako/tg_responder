function request_code() {
    let phone = $("#phone").val();
    let req = new XMLHttpRequest();
    req.open("GET",
        "api/request_code?phone=" + phone,
        true);
    req.send(null);
    req.onload = function(){$("#status").empty();
    $("#status").append(req.responseText);}

}

function auth() {
    let phone = $("#phone").val();
    let code = $("#code").val();
    let password = $("#password").val();
    let url = new URL(window.location.href);
    let group_number = url.searchParams.get("group_number")
    let req = new XMLHttpRequest();
    req.open("GET",
        "api/auth?phone=" + phone + "&code=" + code + "&password=" + password + "&group_number=" + group_number,
        true);
    req.send(null);
    req.onload = function(){
        $("#status").empty();
        $("#status").append(req.responseText);
    }

}