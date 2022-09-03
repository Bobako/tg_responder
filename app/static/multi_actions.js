function multi_actions() {
    if ($("input[type=checkbox]:checked").length != 0) {
        $(".multiple_actions").addClass("multiple_actions_extended");
    }
    else{
        $(".multiple_actions").removeClass("multiple_actions_extended");
    }
}

