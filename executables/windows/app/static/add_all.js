function add_all(){
    $("#status").empty();
    $("#status").append("Аккаунты добавляются...");
    let req = new XMLHttpRequest();
    let url = new URL(window.location.href);
    let group_number = url.searchParams.get("group_number")
    req.open("GET",
        "api/add_sessions?group_number="+group_number,
        true);
    req.send(null);
    req.onload = function (){
        $("#status").empty();
        $("#status").append(req.responseText);
    }
}