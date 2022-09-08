let all_selected = false;
function select_all(class_name=".select_all"){
    if (all_selected){
        $(class_name).prop("checked", false);
        all_selected = false;
    }
    else{
        $(class_name).prop("checked", true);
        all_selected = true;
    }
}