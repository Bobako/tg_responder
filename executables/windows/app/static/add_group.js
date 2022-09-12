function add_group(){
    if ($(".add-group").hasClass("blocked")){
        return;
    }
    let number = $(".group").length;
    $("main").append('<div class="group_container"><div class="group" id=group'+number+'><a class="account add_account" href="add_account?group_number='+number+'">Добавить аккаунт</a></div></div>');
    if (number == 11){
        $(".add-group").addClass("blocked");
    }
}