$(document).ready(function(){
updateNumbers();
})


function drag(e, dragger){
  if (e.button!=0){
  return
  }
  let ball = dragger.parentNode.parentNode;
  let old_group = $(ball.parentElement);
  let old_number = $(ball).attr("number");
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

    let elemBelow = document.elementsFromPoint(event.clientX, event.clientY);
    let new_group = null;
    for (let i=0; i<elemBelow.length; i++){
        if (elemBelow[i].className =="group"){
        new_group = elemBelow[i];}
    }
    if (new_group){
        let new_number = 0;
        let accounts = new_group.childNodes;
        for (let i =0; i < accounts.length; i ++){
            if (accounts[i].className == "account"){
                if (getCoords(accounts[i]).top > event.pageY){
                    break;
                }
                new_number ++;
            }}

        move_account(new_group, new_number, ball, true);
        return;
    }
    move_account(old_group, old_number, ball, false);
  }

}

function move_account(group, number, account, position_changed){
    account.style.position = 'static';
    account = $("body>.account");
    if (number != 0){
        let af =  $(group).find(".account")[number-1];
        account.insertAfter(af);
    }
    else{
        $(account).prependTo(group);
    }
    if (position_changed){
        account.find("input").val(group.id.slice(5))
        updateNumbers();
        }
    }




function getCoords(elem) {   // кроме IE8-
  var box = elem.getBoundingClientRect();
  return {
    top: box.top + pageYOffset,
    left: box.left + pageXOffset
  };
}

function updateNumbers(){
$.ajax({
           type: "POST",
           url: "/api/move_account",
           data: $("#account_number_form").serialize(), // serializes the form's elements.
           success: function(data)
           {
               console.log(data); // show response from the php script.
           }
         });
}