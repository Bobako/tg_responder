function change(selector, changed=true){
    const fields_container = $(selector).parent();
    const type = selector.value;

    const text = (fields_container.find("input")[0]);
    const path = (fields_container.find("input")[1]);
    const ttl =  (fields_container.find("input")[3]);
    const id = ttl.name.slice(0, -4)
    console.log(id);
    if (type == 2 || type == 3){
        $(text).prop("disabled", true)

    }
    else{
        $(text).prop("disabled", false)

    }

    if (type == 0){
        $(path).prop("disabled", true)
        $(ttl).prop("disabled", true)
    }
    else{
        $(path).prop("disabled", false)
        $(ttl).prop("disabled", false)
    }

    if (type == 7){
        $(text).attr("name", id+":latitude")
        $(text).attr("type", "number")
        $(text).attr("placeholder", "Широта")
        $(text).attr("title", "Широта")


        $(path).attr("name", id+":longitude")
        $(path).attr("type", "number")
        $(path).attr("placeholder", "Долгота")
        $(path).attr("title", "Долгота")

        if (changed){
            $(text).val(null)
            $(path).val(null)
        }
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

        if (changed){
            $(text).val(null)
            $(path).val(null)
        }

    }

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