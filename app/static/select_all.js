let all_selected = false;
function select_all(){
    if (all_selected){
        $(".select_all").prop("checked", false);
        all_selected = false;
    }
    else{
        $(".select_all").prop("checked", true);
        all_selected = true;
    }
}