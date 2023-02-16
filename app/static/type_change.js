function change(selector, changed=true){
    const fields_container = $(selector).parent();
    const type = selector.value;

    const text = (fields_container.find("input")[0]);
    const path = (fields_container.find("input")[1]);
    const ttl =  (fields_container.find("input")[3]);
    const id = ttl.name.slice(0, -4)
    if (type == 7){
        $(text).attr("name", id+":latitude")
        $(text).attr("type", "number")
        $(text).attr("placeholder", "Широта")
        $(text).attr("title", "Широта")


        $(path).attr("name", id+":longitude")
        $(path).attr("type", "number")
        $(path).attr("placeholder", "Долгота")
        $(path).attr("title", "Долгота")
    }
    else{
        $(text).attr("name", id+":text")
        $(text).attr("type", "text")
        $(text).attr("placeholder", "Текст")
        $(text).attr("title", "Текст сообщения")

        $(path).attr("name", id+":content_path")
        $(path).attr("type", "text")
        $(path).attr("placeholder", "Путь к содержимому")
        $(path).attr("title", "Путь к содержимому")
    }
    if (type == 2 || type == 3){
        $(text).prop("disabled", true)
        place_dummy(text, "text_dummy", fields_container, true)

    }
    else{
        $(text).prop("disabled", false)
        place_dummy(text, "text_dummy", fields_container, false)
    }

    if (type == 0){
        $(path).prop("disabled", true)
        $(ttl).prop("disabled", true)
        place_dummy(path, "path_dummy", fields_container, true)
        place_dummy(ttl, "ttl_dummy", fields_container, true)
    }
    else{
        $(path).prop("disabled", false)
        $(ttl).prop("disabled", false)
        place_dummy(path, "path_dummy", fields_container, false)
        place_dummy(ttl, "ttl_dummy", fields_container, false)
    }

    if (changed){
            $(text).val(null)
            $(path).val(null)
            $(ttl).val(0)
        }

}

function place_dummy(field, dummy_class, fields_container, place){
        if (place){
        var dummy = $(field).clone()

        $(dummy).prop("disabled", false)
        $(dummy).val(null)
        $(dummy).prop("hidden", true)
        $(dummy).addClass(dummy_class)
        $(fields_container).append(dummy)}
        else{
        $(fields_container).find("."+dummy_class).remove();}

}

function refresh_messages_constraints(){
    let type_changers = $(".type_changer");
    for (let i=0; i<type_changers.length; i++){
        change(type_changers[i], false);
    }
}

$(document).ready(
    refresh_messages_constraints()
)