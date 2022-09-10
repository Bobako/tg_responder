function get_chain(id){
    if (id == "0"){
    return
    }
    let req = new XMLHttpRequest();
    req.open("GET", "api/get_chain?id="+id, true);
    req.send();
    req.onload = function(){
        $("main").empty();
        $("main").append(req.response);
        refresh_messages_constraints()
    };
}

function new_message(button){
    $(button).remove();
    $(".messages").append(
    '<div class="message">'+
    '        <div>'+
    '           <input type="text" step="any" name="NEW:text" placeholder="Текст" title="Текст сообщения"'+
    '                   value="" class="long">'+
    '           <input type="text" step="any" name="NEW:content_path"'+
    '                   placeholder="Путь к содержимому" value="" title="Путь к содержимому" class="long">'+
    '           <input type="number" name="NEW:delay_seconds"'+
    '                   placeholder="Задержка перед отправкой" value=0 title="Задержка перед отправкой" min="0">'+
        '               <input autocomplete="off" type="number" name="NEW:ttl" title="Время жизни"'+
    '                       placeholder="Время жизни" value=0 min="0" max="60">'+
    '            <select name="NEW:type" onchange="change(this)">'+

    '                <option value="0">Текст</option>'+
    '                <option value="1">Фото</option>'+
    '                <option value="2">Голосовое сообщение</option>'+
    '                <option value="3">Видео-сообщение</option>'+
    '                <option value="4">Документ</option>'+
    '                <option value="5">Видео</option>'+
    '                <option value="6">Звуковой файл</option>'+
    '                <option value="7">Местоположение</option>'+
    '            </select>'+
    '        </div>'+
    '        <div>'+
    '            <div class="gg-controller" onmousedown="drag(event, this)"></div>'+
    '        </div>'+
    '    </div>'
    );
    $(".messages").append(button);
}

function change_color(cb){
    if (cb.checked){
       $(cb).parent().css("color", "red");
       }
    else{
    $(cb).parent().css("color", "black");       }
}

function drag(e, dragger){
  if (e.button!=0){
  return
  }
  let ball = dragger.parentNode.parentNode;
  ball.style.width = ball.offsetWidth +"px";
  var coords = getCoords(ball);
  var shiftX = e.pageX - coords.left;
  var shiftY = e.pageY - coords.top;

  ball.style.position = 'absolute';
  document.body.appendChild(ball);
  moveAt(e);

  ball.style.zIndex = 1000;

  function moveAt(e) {
    ball.style.left = e.pageX - shiftX + 'px';
    ball.style.top = e.pageY - shiftY + 'px';
  }

  document.onmousemove = function(e) {
    moveAt(e);
  };

  ball.onmouseup = function() {
        document.onmousemove = null;
        ball.onmouseup = null;



        let new_number = 0;
        let messages = document.getElementById("messages");
        let accounts = messages.childNodes;
        for (let i =0; i < accounts.length; i ++){
            if (accounts[i].className == "message"){
                if (getCoords(accounts[i]).top > event.clientY){
                    break;
                }
                new_number ++;
            }
        }

        move_account(messages, new_number, ball);

    }
}

function move_account(group, number, account){
    account.style.position = 'static';
    account = $(account);
    if (number != 0){
        let af =  $(group).find(".message")[number-1];
        account.insertAfter(af);
    }
    else{
    $(account).prependTo(group);
    }


}


function getCoords(elem) {   // кроме IE8-
  var box = elem.getBoundingClientRect();
  return {
    top: box.top + pageYOffset,
    left: box.left + pageXOffset
  };
}

function new_chain(account_id){
    let req = new XMLHttpRequest();
    req.open("GET", "api/new_chain?account_id="+account_id, true);
    req.send();
    req.onload = function(){
           const new_chain_id = req.response;
           console.log($(".chains_container"))
           $("#chains_container").append(
            '<div class="select_chain">'+
                '<div class="chain_name" onclick="get_chain('+new_chain_id+')">Новая цепочка</div>'+
                '<div><input type="checkbox" class="ma" id="cb'+new_chain_id+'" onclick="multi_actions()"></div>'+
            '</div>'
            )
            get_chain(new_chain_id);
    };


}