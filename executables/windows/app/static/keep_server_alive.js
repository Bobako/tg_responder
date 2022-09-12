$(document).ready(function(){
    setInterval(keep_alive, 3000)
});

function keep_alive(){
    let req = new XMLHttpRequest();
    req.open("GET", "/flaskwebgui-keep-server-alive", true);
    //req.overrideMimeType("application/json");
    req.send();
    req.onload = function(){
        console.log(req.response)
    };
}