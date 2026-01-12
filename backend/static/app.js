async function changeStatus(orderId, status) {
    const res = await fetch("/status", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            id: orderId,
            status: status
        })
    });

    if (res.ok) {
        const card = document.getElementById("order-" + orderId);
        card.style.opacity = "0.4";

        setTimeout(() => {
            card.remove();
        }, 400);
    } else {
        alert("Ошибка смены статуса");
    }
}
