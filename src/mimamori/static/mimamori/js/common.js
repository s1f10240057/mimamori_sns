const getData = async(targetValue, url) =>{
    const token = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const response = await fetch(url, {
      method: 'POST',
        headers: {
            'X-CSRFToken': token
        },
        body: 
            JSON.stringify({'target': targetValue}),
    });

    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    const data = await response.json();
    return data;
}

const putData = (lstId, data, isLink = false) => {
    const lstBoard = document.getElementById(lstId);
    lstBoard.innerHTML = '';
    if (!data.notificationLst){
        return;
    }
    for(const i of data.notificationLst){
        const Element = document.createElement(isLink ? "a" : "div");
        if (isLink === true){
            Element.href="{% url 'mimamori:doTask' task_id = {{i.id}} %}"
        }
        Element.textContent = `時間: ${i.notify_at}, テーマ: ${i.task_theme}, ${i.task_ended ? "終わった": "まだ"}`;
        
        lstBoard.appendChild(Element);
    }
}

export { getData, putData}